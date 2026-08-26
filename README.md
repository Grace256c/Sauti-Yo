# Sauti-Yo
Sauti Yo. A phone-first Rights-to-Action platform making verified legal information accessible through USSD, SMS and Voice.

## Backend conventions

### Linking ChannelContent to a Situation

`ChannelContent` (in `apps/content`) is intentionally not connected to
`Situation` by a foreign key — it's a flexible, general-purpose model for
any piece of channel-specific text. To link a `ChannelContent` entry to a
specific situation, use this naming convention for `content_key`:

    {situation_slug_with_underscores}_intro

Example: the situation with slug `home-safety` has its channel intros
stored under `content_key="home_safety_intro"`.

Use `apps.rights.services.get_channel_text(situation_slug, channel, language)`
to look this up safely — it handles the naming convention for you and
returns `None` (not an error) if no content exists yet for that
situation/channel/language combination.
