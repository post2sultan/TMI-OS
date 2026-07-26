import json
import unittest

from app.services.analysis.parser import AnalysisParser
from app.services.scoring.framework import (
    ScoringDimensionName,
)


class AnalysisParserTests(unittest.TestCase):

    def test_normalizes_local_model_field_variants(
        self,
    ) -> None:
        dimensions = []

        for dimension in ScoringDimensionName:
            dimensions.append(
                {
                    "dimension_name": (
                        dimension.value.replace(
                            "_",
                            " ",
                        ).title()
                    ),
                    "score": 75,
                    "confidence": 0.8,
                    "reasoning": (
                        "The campaign article provides "
                        "specific supporting detail."
                    ),
                    "description": "",
                    "recommendations": [],
                    "evidence": [
                        {
                            "description": (
                                "A campaign-specific fact "
                                "supports this assessment."
                            ),
                        },
                        {
                            "url": "Campaign URL",
                            "description": (
                                "Another campaign-specific fact."
                            ),
                        },
                        {
                            "description": " ",
                        },
                    ],
                }
            )

        assessment = AnalysisParser().parse(
            json.dumps(
                {
                    "campaign_id": 71,
                    "framework_version": "v1.0",
                    "dimensions": dimensions,
                    "summary": "",
                    "strengths": [],
                    "weaknesses": [],
                    "recommendations": [],
                }
            )
        )

        self.assertEqual(
            {
                item.dimension
                for item in assessment.dimensions
            },
            set(ScoringDimensionName),
        )
        self.assertTrue(
            all(
                len(item.evidence) == 2
                and str(item.evidence[0].url)
                == "https://unknown.local/"
                and str(item.evidence[1].url)
                == "https://unknown.local/"
                for item in assessment.dimensions
            )
        )
        self.assertEqual(
            len(assessment.recommendations),
            1,
        )
        self.assertIn(
            "Improve the lowest-scoring dimension",
            assessment.recommendations[0],
        )
        self.assertEqual(
            assessment.framework_version,
            "1.0",
        )
        self.assertIn(
            "campaign article",
            assessment.summary,
        )
        self.assertIn(
            "Highest-scoring dimension",
            assessment.strengths[0],
        )
        self.assertIn(
            "Lowest-scoring dimension",
            assessment.weaknesses[0],
        )


if __name__ == "__main__":
    unittest.main()
