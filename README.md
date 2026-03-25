# Google Maps Lead Enrichment Actor

**Category:** Lead Generation | Business Intelligence
**Pricing Target:** $0.10–0.20 per enrichment run
**Input:** Google Maps place objects from `google-maps-scraper`
**Output:** Enriched B2B leads with emails, phones, social media

## How It Works

1. Takes Google Maps place data (from your existing `google-maps-scraper`)
2. Visits each business's website
3. Extracts:
   - 📧 Email addresses (pattern-matched from HTML)
   - 📞 Phone numbers (multiple formats)
   - 🔗 Social media links (Facebook, Instagram, LinkedIn, Twitter, WeChat, etc.)
   - ⭐ Lead score (0–100 quality rating)

## Input Schema

```json
{
  "googleMapsData": [
    {
      "name": "Acme Corp",
      "address": "123 Main St",
      "website": "https://acmecorp.com"
    }
  ],
  "enrichmentLevel": "full"
}
```

## Output Schema

```json
{
  "name": "Acme Corp",
  "address": "123 Main St",
  "enriched": {
    "website": "https://acmecorp.com",
    "emails": ["contact@acmecorp.com", "sales@acmecorp.com"],
    "phones": ["+1-555-123-4567"],
    "socialMedia": {
      "linkedin": "https://linkedin.com/company/acmecorp",
      "facebook": "https://facebook.com/acmecorp"
    },
    "leadScore": 85
  }
}
```

## Use Cases

- **B2B Sales Teams**: Build prospect lists from Google Maps categories
- **Recruiters**: Find company contact info for hiring pipelines
- **Market Research**: Map entire business categories with full contact data
- **Cold Outreach**: Fuel email/LinkedIn campaigns with verified leads

## Revenue Model

- **Pay-per-result**: $0.10 (basic) / $0.20 (full enrichment)
- **Volume tiers**: 1000+ runs/month = discounted rate
- **API access**: Add 50% premium for direct API access

## Competitive Advantage

| Feature | Generic Scraper | This Actor |
|---------|-----------------|------------|
| Google Maps native | ❌ | ✅ |
| Website email extraction | ❌ | ✅ |
| Social media links | ❌ | ✅ |
| Lead scoring | ❌ | ✅ |
| WeChat/Weixin support | ❌ | ✅ |

## Notes

- Works best with output from `shuicici/google-maps-scraper`
- Supports concurrent enrichment (up to 20 places per run)
- Rate limiting respects target websites' robots.txt
