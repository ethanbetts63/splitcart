from django.core.management.base import BaseCommand
from products.models import SuperCategory, Bargain
from companies.models import Category

class Command(BaseCommand):
    help = 'Creates SuperCategory instances and associates them with existing Category instances based on a hardcoded dictionary.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Deleting all existing SuperCategory instances..."))
        SuperCategory.objects.all().delete()

        splitcart_super_categories = {
            "Everyday Essentials": [
                252, 1647, 2597, 72, 786, 1672, 2144,
                25, 592, 1694, 2021, 1622, 2294, 1658, 2706
            ],
            "Pantry Power-Ups": [
                87, 635, 1428, 1899, 143, 1217, 2268,
                583, 1401, 2652, 406, 1321, 2570,
                420, 1325, 2368, 96, 1071, 1411, 115,
                346, 1297, 2725, 1294, 2620, 301, 2296,
                469, 1354, 2750, 1440, 108
            ],
            "Little Luxuries": [
                465, 1350, 1929, 849, 1509, 2018, 797, 1482, 1472,
                107, 487, 2028, 1227, 706, 207, 78, 480, 1356, 2592,
                411, 1323, 2752, 813, 484, 1987, 1291, 47, 1935,
                733, 1455, 2216, 359, 1305, 2629, 1337, 2782,
                358, 1304, 2707, 832, 1497, 2551, 752, 1660,
                2310, 723, 2722, 764, 1665
            ],
            "Drinks & Delights": [
                17, 1126, 1365, 1997, 136, 1601, 2139, 570, 1682, 2101,
                507, 1896, 427, 1620, 2253, 1165, 1602, 2159, 1112, 1489,
                2019, 1129, 1520, 2158, 1092, 1317, 1857, 1081, 1370, 1919,
                1090, 1569, 2327, 1266, 2324, 1139, 162, 1216, 1971,
                1127, 1309, 1922, 1098, 1576, 2006, 1100, 1351, 2013,
                1107, 1270, 1872, 1077, 1542, 1955, 1114, 1302, 1907,
                1082, 1287, 1138, 1594, 1866, 1119, 1327, 2753, 1385
            ]
        }

        for super_category_name, category_ids in splitcart_super_categories.items():
            super_category, created = SuperCategory.objects.get_or_create(name=super_category_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created SuperCategory: {super_category_name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"SuperCategory already exists: {super_category_name}"))

            super_category.categories.clear()

            for cat_id in category_ids:
                try:
                    category = Category.objects.get(id=cat_id)
                    super_category.categories.add(category)
                    self.stdout.write(self.style.SUCCESS(f"  Added Category '{category.name}' (ID: {cat_id}) to {super_category_name}"))
                except Category.DoesNotExist:
                    self.stderr.write(self.style.WARNING(f"  Category with ID {cat_id} not found for {super_category_name}"))

        self.stdout.write(self.style.SUCCESS("Associating Bargains with SuperCategories..."))
        for super_category in SuperCategory.objects.all():
            for category in super_category.categories.all():
                bargains = Bargain.objects.filter(product__category=category)
                for bargain in bargains:
                    bargain.super_categories.add(super_category)
                    self.stdout.write(self.style.SUCCESS(f"  Associated bargain for '{bargain.product.name}' with '{super_category.name}'"))

        self.stdout.write(self.style.SUCCESS("SuperCategory creation and association complete."))
