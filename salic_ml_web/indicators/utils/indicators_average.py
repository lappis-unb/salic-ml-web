def fetch_weighted_complexity(metrics):
    metrics_weights = {
        'items': 1,
        'to_verify_funds': 5,
        'proponent_projects': 2,
        'new_provders': 1,
        'verified_approved': 2,
        'raised_funds': 0,
        'verified_funds': 0,
        'approved_funds': 0,
        'common_items_ratio': 0,
        'total_receipts': 0,
        'items_prices': 0
    }

    max_total = sum([metrics_weights[metric_name] for metric_name in metrics_weights])

    total = 0

    for metric_name in metrics_weights:
        try:
            if metrics[metric_name] is not None:
                if metrics[metric_name]['is_outlier']:
                    total += metrics_weights[metric_name]
        except KeyError:
            pass

    value = total/max_total

    return 1 - value