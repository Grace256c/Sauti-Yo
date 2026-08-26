# Sauti-Yo

Sauti Yo. A phone-first Rights-to-Action platform making verified legal information accessible through USSD, SMS and Voice.

## Rights-to-Action API

The backend exposes a Rights-to-Action API used by the citizen-facing web experience and by channel integrations such as USSD, SMS and Voice.

### Issue outcome

```http
GET /api/rights/outcomes/{category_slug}/{issue_slug}/


Example:

```http
GET /api/rights/outcomes/work-employment/unpaid/
```

A successful response includes:

- the issue outcome heading and introduction
- evidence items
- the linked situation, where available
- linked rights topics
- action steps
- safety responses
- support/referral services
- verification metadata for rights content

If the category/issue pair does not exist or is inactive, the endpoint returns `404`.

### Other rights endpoints

```http
GET /api/rights/situations/
GET /api/rights/situations/{slug}/
GET /api/rights/topics/
GET /api/rights/topics/{slug}/
```

### Channel content

Channel-specific and language-specific content is available through:

```http
GET /api/content/?content_key={key}&language={language}&channel={channel}
```

Supported channels currently include:

- `web`
- `ussd`
- `sms`
- `voice`

### Support services

Support/referral information is exposed through:

```http
GET /api/support/
```

The Rights-to-Action engine follows this general flow:

```text
IssueOutcome
    ↓
Situation
    ↓
RightsTopic
    ↓
ActionStep / SafetyResponse
    ↓
SupportService
```

Frontend and channel clients should use `category_slug + issue_slug` as the stable identifier for a citizen issue outcome.