class TripCostEstimator:
    """
    Algorithm 2: Smart Trip Cost Estimation

    Steps:
    1. Start with package base price.
    2. Multiply it by number of travelers.
    3. Add transport charge according to selected mode.
    4. Add hotel upgrade charge according to hotel type.
    5. Add meal cost according to travel days.
    6. Apply simple group discount when travelers are 4 or more.

    Time Complexity: O(1)
    because each calculation uses fixed values only once.
    """

    TRANSPORT_COST = {
        'Bus': 500,
        'Tourist Bus': 800,
        'Jeep': 1800,
        'Flight': 7000
    }

    HOTEL_COST = {
        'Standard': 1000,
        'Deluxe': 2200,
        'Resort': 2800,
        'Tea House': 900,
        'Homestay': 700
    }

    MEAL_COST = {
        'Breakfast': 250,
        'Half Board': 600,
        'Full Board': 1000
    }

    def calculate_total(self, base_price, travelers, days, transport_choice, hotel_choice, meal_plan):
        transport_rate = self.TRANSPORT_COST.get(transport_choice, 500)
        hotel_rate = self.HOTEL_COST.get(hotel_choice, 1000)
        meal_rate = self.MEAL_COST.get(meal_plan, 250)

        package_subtotal = float(base_price) * travelers
        transport_total = transport_rate * travelers
        hotel_total = hotel_rate * travelers * max(days - 1, 1)
        meal_total = meal_rate * travelers * days
        gross_total = package_subtotal + transport_total + hotel_total + meal_total

        discount = 0
        if travelers >= 6:
            discount = gross_total * 0.10
        elif travelers >= 4:
            discount = gross_total * 0.05

        final_total = gross_total - discount

        return {
            'package_subtotal': round(package_subtotal, 2),
            'transport_total': round(transport_total, 2),
            'hotel_total': round(hotel_total, 2),
            'meal_total': round(meal_total, 2),
            'gross_total': round(gross_total, 2),
            'discount': round(discount, 2),
            'final_total': round(final_total, 2)
        }
