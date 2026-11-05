class ROICalculator:
    def __init__(
        self,
        grading_fee: float = 25.0,        # Standard PSA Value/Bulk tier cost
        inbound_shipping: float = 4.50,   # Shipping from eBay seller to you
        grading_shipping_ins: float = 5.50, # Split return shipping & insurance per card in batch
        marketplace_fee_pct: float = 0.1325, # eBay standard 13.25% fee on sports cards
        min_net_profit: float = 40.0,     # Minimum dollar profit required to trigger a buy
        min_roi_pct: float = 35.0         # Minimum percentage return required
    ):
        self.grading_fee = grading_fee
        self.inbound_shipping = inbound_shipping
        self.grading_shipping_ins = grading_shipping_ins
        self.marketplace_fee_pct = marketplace_fee_pct
        self.min_net_profit = min_net_profit
        self.min_roi_pct = min_roi_pct

    def evaluate_deal(
        self,
        raw_price: float,
        psa10_comp: float,
        psa9_comp: float = 0.0,
        gem_probability: float = 0.65
    ) -> dict:
        """
        Calculates all-in cost, net payout after fees, PSA 10 ROI,PSA 9 downside,
        and probability-weighted Expected Value (EV).
        """
        # 1. Total All-In Cost Basis
        all_in_cost = round(
            raw_price + self.inbound_shipping + self.grading_fee + self.grading_shipping_ins, 2
        )

        # 2. Net Payouts After Marketplace Fees
        psa10_net_payout = round(psa10_comp * (1.0 - self.marketplace_fee_pct), 2)
        psa9_net_payout = round(psa9_comp * (1.0 - self.marketplace_fee_pct), 2) if psa9_comp > 0 else 0.0

        # 3. Net Profit & ROI (PSA 10 Scenario)
        psa10_profit = round(psa10_net_payout - all_in_cost, 2)
        psa10_roi_pct = round((psa10_profit / all_in_cost) * 100, 1) if all_in_cost > 0 else 0.0

        # 4. Downside Protection (PSA 9 Scenario)
        psa9_profit = round(psa9_net_payout - all_in_cost, 2) if psa9_comp > 0 else round(-all_in_cost, 2)

        # 5. Probability-Weighted Expected Value (EV)
        # Protects your float if a card passes 55/45 centering but gets dinged to a 9 on surface
        expected_profit = round(
            (psa10_profit * gem_probability) + (psa9_profit * (1.0 - gem_probability)), 2
        )
        expected_roi_pct = round((expected_profit / all_in_cost) * 100, 1) if all_in_cost > 0 else 0.0

        # 6. Deal Verdict
        is_viable_flip = (psa10_profit >= self.min_net_profit) and (psa10_roi_pct >= self.min_roi_pct)

        return {
            "raw_price": raw_price,
            "all_in_cost": all_in_cost,
            "psa10_comp": psa10_comp,
            "psa10_net_payout": psa10_net_payout,
            "psa10_profit": psa10_profit,
            "psa10_roi_pct": psa10_roi_pct,
            "psa9_comp": psa9_comp,
            "psa9_profit": psa9_profit,
            "expected_profit_ev": expected_profit,
            "expected_roi_pct": expected_roi_pct,
            "is_viable_flip": is_viable_flip
        }
