class RecommendationEngine:
    """
    Algorithm 1: Tour Recommendation Algorithm

    Logic used:
    1. Find the categories and seasons that the user booked before.
    2. Give higher score to packages from similar categories.
    3. Give extra score to featured packages.
    4. Prefer packages with a medium budget range so that suggestions look practical.
    5. Return top scored packages that the user has not booked yet.

    Time Complexity: O(p + b)
    p = number of packages
    b = number of bookings by the current user
    """

    def get_recommendations(self, user_id, conn, top_n=3):
        bookings = conn.execute(
            '''
            SELECT p.category, p.season, AVG(b.total_amount) AS avg_budget
            FROM bookings b JOIN packages p ON b.package_id = p.id
            WHERE b.user_id=?
            GROUP BY p.category, p.season
            ''',
            (user_id,)
        ).fetchall()

        booked_package_ids = {
            row['package_id'] for row in conn.execute('SELECT package_id FROM bookings WHERE user_id=?', (user_id,)).fetchall()
        }
        packages = conn.execute('SELECT * FROM packages ORDER BY featured DESC, id DESC').fetchall()

        if not bookings:
            return packages[:top_n]

        liked_categories = {row['category'] for row in bookings}
        liked_seasons = {row['season'] for row in bookings}
        budgets = [row['avg_budget'] for row in bookings if row['avg_budget']]
        avg_budget = sum(budgets) / len(budgets) if budgets else 12000

        scored = []
        for package in packages:
            if package['id'] in booked_package_ids:
                continue
            score = 0
            if package['category'] in liked_categories:
                score += 5
            if package['season'] in liked_seasons:
                score += 2
            if package['featured']:
                score += 2
            price_gap = abs(float(package['price']) - float(avg_budget))
            if price_gap <= 5000:
                score += 3
            elif price_gap <= 12000:
                score += 1
            if package['days'] <= 3:
                score += 1
            scored.append((score, package))

        scored.sort(key=lambda item: (item[0], item[1]['featured'], -item[1]['price']), reverse=True)
        return [item[1] for item in scored[:top_n]]
