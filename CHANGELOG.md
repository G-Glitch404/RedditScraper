# Changelog

All notable changes to **The Ultimate Reddit Scraper** will be documented in this file, for all the next releases.

## [1.0.0] - 2026-06-15

### Added
- Initial public release of **The Ultimate Reddit Scraper**
- Support for scraping subreddits URLs, posts URLs, users URLs, and custom feeds URLs, and search URLs with all of Reddit's filters can be applied 
- Deep crawling feature for scraping a post's comments section when providing a post url
- Keyword filtering for post selection
- Field-based filtering for output control
- Crosspost inclusion or exclusion
- Removed posts/comments inclusion or exclusion
- Optional cookie-based authenticated scraping
- Proxy configuration support
- Media extraction for:
  - single images
  - gallery posts
  - video posts
  - preview media links
- Structured post output with:
  - post metadata
  - author data
  - subreddit data
  - engagement metrics
  - removal and moderation flags
  - comment section

### Changed
- had to remove replies from comments deep crawling (will be adding it later)
- deep crawling is only for top level comments on a post (means only the post's comments not their replies)

### Fixed
- None

### Notes
- This is the first official release of the actor.
- max amount of urls can be provided for the actor are 25 urls
- Future versions will expand crawling reliability, output normalization, and media handling.
- next version release will include comment's replies crawling
- cookies might set to be required for later versions so crawling will be account based but happy news Reddit won't block any accounts so no need to worry about your account getting banned nor about using a freshly created account
