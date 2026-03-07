import pytest
from companies.models import Category
from companies.tests.factories import CompanyFactory, CategoryFactory
from products.tests.factories import ProductFactory
from data_management.database_updating_classes.product_updating.category_manager import CategoryManager


def _make_caches(categories=None, products_by_norm_string=None):
    return {
        'categories': categories or {},
        'products_by_norm_string': products_by_norm_string or {},
    }


def _raw(norm_string, category_path):
    return [{'product': {'normalized_name_brand_size': norm_string, 'category_path': category_path}}]


@pytest.mark.django_db
class TestCategoryManagerCreateNewCategories:
    def test_creates_missing_categories(self, mock_command):
        company = CompanyFactory()
        caches = _make_caches()
        manager = CategoryManager(mock_command, caches, lambda name, key, val: caches[name].__setitem__(key, val))
        paths = {('Dairy', 'Milk')}
        manager._create_new_categories(paths, company)

        assert Category.objects.filter(name='Dairy', company=company).exists()
        assert Category.objects.filter(name='Milk', company=company).exists()

    def test_does_not_recreate_existing_categories(self, mock_command):
        company = CompanyFactory()
        existing = CategoryFactory(company=company, name='Dairy')
        caches = _make_caches(categories={('Dairy', company.id): existing})
        manager = CategoryManager(mock_command, caches, lambda name, key, val: caches[name].__setitem__(key, val))
        paths = {('Dairy',)}
        manager._create_new_categories(paths, company)

        assert Category.objects.filter(name='Dairy', company=company).count() == 1

    def test_updates_cache_after_creation(self, mock_command):
        company = CompanyFactory()
        caches = _make_caches()
        manager = CategoryManager(mock_command, caches, lambda name, key, val: caches[name].__setitem__(key, val))
        paths = {('Snacks',)}
        manager._create_new_categories(paths, company)

        assert ('Snacks', company.id) in caches['categories']


@pytest.mark.django_db
class TestCategoryManagerCreateParentChildLinks:
    def test_creates_parent_child_link(self, mock_command):
        company = CompanyFactory()
        parent = CategoryFactory(company=company, name='Dairy')
        child = CategoryFactory(company=company, name='Milk')
        caches = _make_caches(categories={
            ('Dairy', company.id): parent,
            ('Milk', company.id): child,
        })
        manager = CategoryManager(mock_command, caches, lambda *a: None)
        paths = {('Dairy', 'Milk')}
        manager._create_parent_child_links(paths, company)

        assert parent in child.parents.all()

    def test_does_not_duplicate_existing_links(self, mock_command):
        company = CompanyFactory()
        parent = CategoryFactory(company=company, name='Dairy')
        child = CategoryFactory(company=company, name='Milk')
        child.parents.add(parent)
        caches = _make_caches(categories={
            ('Dairy', company.id): parent,
            ('Milk', company.id): child,
        })
        manager = CategoryManager(mock_command, caches, lambda *a: None)
        paths = {('Dairy', 'Milk')}
        manager._create_parent_child_links(paths, company)

        assert child.parents.filter(pk=parent.pk).count() == 1

    def test_single_element_path_creates_no_links(self, mock_command):
        company = CompanyFactory()
        cat = CategoryFactory(company=company, name='Dairy')
        caches = _make_caches(categories={('Dairy', company.id): cat})
        manager = CategoryManager(mock_command, caches, lambda *a: None)
        paths = {('Dairy',)}
        manager._create_parent_child_links(paths, company)

        assert cat.parents.count() == 0


@pytest.mark.django_db
class TestCategoryManagerLinkProductsToCategories:
    def test_links_product_to_leaf_category(self, mock_command):
        company = CompanyFactory()
        product = ProductFactory()
        leaf = CategoryFactory(company=company, name='Milk')
        caches = _make_caches(
            categories={('Milk', company.id): leaf},
            products_by_norm_string={product.normalized_name_brand_size: product.id},
        )
        manager = CategoryManager(mock_command, caches, lambda *a: None)
        raw = _raw(product.normalized_name_brand_size, ['Dairy', 'Milk'])
        manager._link_products_to_categories(raw, company)

        product.refresh_from_db()
        assert product.category.filter(pk=leaf.pk).exists()

    def test_does_not_duplicate_existing_link(self, mock_command):
        company = CompanyFactory()
        product = ProductFactory()
        leaf = CategoryFactory(company=company, name='Milk')
        product.category.add(leaf)
        caches = _make_caches(
            categories={('Milk', company.id): leaf},
            products_by_norm_string={product.normalized_name_brand_size: product.id},
        )
        manager = CategoryManager(mock_command, caches, lambda *a: None)
        raw = _raw(product.normalized_name_brand_size, ['Dairy', 'Milk'])
        manager._link_products_to_categories(raw, company)

        assert product.category.filter(pk=leaf.pk).count() == 1


@pytest.mark.django_db
class TestCategoryManagerProcess:
    def test_process_returns_early_when_no_category_paths(self, mock_command):
        company = CompanyFactory()
        caches = _make_caches()
        manager = CategoryManager(mock_command, caches, lambda *a: None)
        raw = [{'product': {'normalized_name_brand_size': 'milk', 'category_path': None}}]
        manager.process(raw, company)  # Should not raise
        assert Category.objects.filter(company=company).count() == 0

    def test_process_end_to_end_creates_categories_and_links(self, mock_command):
        company = CompanyFactory()
        product = ProductFactory()
        caches = _make_caches(products_by_norm_string={product.normalized_name_brand_size: product.id})
        manager = CategoryManager(
            mock_command, caches,
            lambda name, key, val: caches[name].__setitem__(key, val)
        )
        raw = _raw(product.normalized_name_brand_size, ['Dairy', 'Milk'])
        manager.process(raw, company)

        dairy = Category.objects.get(name='Dairy', company=company)
        milk = Category.objects.get(name='Milk', company=company)
        assert dairy in milk.parents.all()
        assert product.category.filter(pk=milk.pk).exists()
