from app.services.pipeline.pipeline import pipeline

campaigns = pipeline.discover_and_extract(
    "STC Saudi Arabia"
)

print("=" * 80)
print(f"Campaigns: {len(campaigns)}")
print("=" * 80)

for i, campaign in enumerate(campaigns, start=1):

    print()

    print(f"[{i}]")

    print("ID:", campaign.id)

    print("TITLE:", campaign.title)

    print("SOURCE:", campaign.source)

    print("URL:", campaign.url)

    print("CONTENT WORDS:", len(campaign.content.split()))