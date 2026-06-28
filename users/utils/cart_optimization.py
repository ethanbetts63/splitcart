from rest_framework.response import Response
from rest_framework import status
from companies.models import Company
from data_management.utils.cart_optimization import (
    calculate_optimized_cost, calculate_baseline_cost,
    build_price_slots, calculate_best_single_store
)
from products.utils.default_companies import get_default_company_ids


def _build_optimization_results(price_slots, baseline_cost, max_company_options):
    results = []
    for max_companies in max_company_options:
        optimized_cost, shopping_plan, _ = calculate_optimized_cost(price_slots, max_companies)
        if optimized_cost is None:
            continue

        actual_used = sum(1 for plan in shopping_plan.values() if plan['items'])
        if actual_used != max_companies:
            continue

        savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
        results.append({
            'max_companies': max_companies,
            'optimized_cost': optimized_cost,
            'savings': savings,
            'shopping_plan': shopping_plan,
        })
    return results


def run_cart_optimization(cart_obj, max_company_options):
    company_ids = get_default_company_ids()
    if not company_ids:
        return Response({'error': 'No pricing companies configured.'}, status=status.HTTP_400_BAD_REQUEST)

    companies = Company.objects.filter(id__in=company_ids)

    original_items = []
    cart_with_substitutes_slots = []
    for item in cart_obj.items.all():
        original_items.append({'product': {'id': item.product.id}, 'quantity': item.quantity})

        approved_subs = item.chosen_substitutions.filter(is_approved=True)
        if approved_subs.exists():
            slot = [{'product_id': sub.substituted_product.id, 'quantity': sub.quantity} for sub in approved_subs]
        else:
            slot = [{'product_id': item.product.id, 'quantity': item.quantity}]
        cart_with_substitutes_slots.append(slot)

    try:
        simple_cart = [[{'product_id': item['product']['id'], 'quantity': item['quantity']}] for item in original_items]
        simple_price_slots = build_price_slots(simple_cart, companies)
        if not simple_price_slots:
            return Response(
                {'error': 'Could not find prices for items in your cart.'},
                status=status.HTTP_404_NOT_FOUND
            )
        baseline_cost = calculate_baseline_cost(simple_price_slots)

        subs_price_slots = build_price_slots(cart_with_substitutes_slots, companies)
        subs_optimization_results = []
        if subs_price_slots:
            subs_optimization_results = _build_optimization_results(
                subs_price_slots,
                baseline_cost,
                max_company_options
            )
            subs_best_single_company = calculate_best_single_store(subs_price_slots, cart_with_substitutes_slots)
        else:
            subs_best_single_company = None

        no_subs_optimization_results = _build_optimization_results(
            simple_price_slots,
            baseline_cost,
            max_company_options
        )
        no_subs_best_single_company = calculate_best_single_store(simple_price_slots, simple_cart)

        return Response({
            'baseline_cost': baseline_cost,
            'optimization_results': subs_optimization_results,
            'best_single_company': subs_best_single_company,
            'no_subs_results': {
                'baseline_cost': baseline_cost,
                'optimization_results': no_subs_optimization_results,
                'best_single_company': no_subs_best_single_company,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'An unexpected error occurred: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
