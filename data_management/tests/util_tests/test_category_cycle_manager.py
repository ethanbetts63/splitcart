import pytest
from data_management.database_updating_classes.product_updating.post_processing.category_cycle_manager import CategoryCycleManager
from companies.tests.factories import CategoryFactory, CompanyFactory


@pytest.mark.django_db
class TestCategoryCycleManager:
    def test_no_cycles_reports_zero_repairs(self, mock_command):
        company = CompanyFactory()
        parent = CategoryFactory(company=company)
        child = CategoryFactory(company=company)
        child.parents.add(parent)

        manager = CategoryCycleManager(mock_command, company)
        manager.prune_cycles()

        assert manager.cycles_repaired == 0

    def test_detects_and_prunes_simple_cycle(self, mock_command):
        company = CompanyFactory()
        a = CategoryFactory(company=company)
        b = CategoryFactory(company=company)
        # A → B and B → A creates a cycle
        a.parents.add(b)
        b.parents.add(a)

        manager = CategoryCycleManager(mock_command, company)
        manager.prune_cycles()

        assert manager.cycles_repaired >= 1

    def test_after_pruning_no_cycle_remains(self, mock_command):
        company = CompanyFactory()
        a = CategoryFactory(company=company)
        b = CategoryFactory(company=company)
        a.parents.add(b)
        b.parents.add(a)

        manager = CategoryCycleManager(mock_command, company)
        manager.prune_cycles()

        # After pruning, at least one direction of the cycle must be gone
        a.refresh_from_db()
        b.refresh_from_db()
        a_parents = list(a.parents.all())
        b_parents = list(b.parents.all())
        # They can't both still point to each other
        assert not (b in a_parents and a in b_parents)

    def test_empty_company_runs_without_error(self, mock_command):
        company = CompanyFactory()
        manager = CategoryCycleManager(mock_command, company)
        manager.prune_cycles()  # Should not raise
        assert manager.cycles_repaired == 0

    def test_self_loop_is_pruned(self, mock_command):
        company = CompanyFactory()
        a = CategoryFactory(company=company)
        a.parents.add(a)

        manager = CategoryCycleManager(mock_command, company)
        manager.prune_cycles()

        a.refresh_from_db()
        assert a not in a.parents.all()
        assert manager.cycles_repaired >= 1

    def test_only_repairs_cycles_for_given_company(self, mock_command):
        company_a = CompanyFactory()
        company_b = CompanyFactory()

        # Cycle in company_b
        b1 = CategoryFactory(company=company_b)
        b2 = CategoryFactory(company=company_b)
        b1.parents.add(b2)
        b2.parents.add(b1)

        # No cycle in company_a
        a1 = CategoryFactory(company=company_a)

        manager = CategoryCycleManager(mock_command, company_a)
        manager.prune_cycles()

        # company_a has no cycles, company_b cycle is untouched
        assert manager.cycles_repaired == 0
        b1.refresh_from_db()
        assert b2 in b1.parents.all()
