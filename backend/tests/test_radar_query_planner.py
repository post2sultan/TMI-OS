import unittest

from app.services.radar_query_planner import QueryPlanInput, RadarQueryPlanner


class RadarQueryPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = RadarQueryPlanner()

    def test_brief_expands_into_bounded_bilingual_queries(self) -> None:
        queries = self.planner.plan(QueryPlanInput(brief="Saudi retail campaigns"))
        self.assertLessEqual(len(queries), 8)
        self.assertEqual(queries[0], "Saudi retail campaigns")
        self.assertTrue(any("حملة" in query for query in queries))

    def test_watchlist_combines_entities_terms_and_market(self) -> None:
        queries = self.planner.plan(QueryPlanInput(brands=["Brand A"], locations=["Riyadh"], campaign_terms=["launch", "activation"]))
        self.assertTrue(any("Brand A" in query and "Riyadh" in query for query in queries))
        self.assertTrue(any("حملة" in query for query in queries))

    def test_duplicate_inputs_do_not_duplicate_queries(self) -> None:
        queries = self.planner.plan(QueryPlanInput(brands=["Brand A", "brand a"], campaign_terms=["launch", "launch"]))
        self.assertEqual(len(queries), len({query.casefold() for query in queries}))


if __name__ == "__main__":
    unittest.main()
