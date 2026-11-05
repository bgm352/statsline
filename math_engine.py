def calculate_arbitrage_metrics(raw_cost, grading_fee=66.40, psa_10_payout=280.00):
  total_basis = raw_cost + grading_fee
  net_profit = psa_10_payout - total_basis
  roi = (net_profit / total_basis) * 100

  is_valid = total_basis * 2 <= psa_10_payout  # 2x EV Multiplier Rule

  return {
      "total_basis": round(total_basis, 2),
      "net_profit": round(net_profit, 2),
      "roi_percent": round(roi, 1),
      "satisfies_2x_rule": is_valid,
  }
