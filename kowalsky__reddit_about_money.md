# kowalsky/reddit_about_money (dataset)

```json
{
  "kind": "dataset",
  "id": "kowalsky/reddit_about_money",
  "url": "https://huggingface.co/datasets/kowalsky/reddit_about_money",
  "meta": {
    "tags": [
      "task_categories:text-generation",
      "language:en",
      "size_categories:n<1K",
      "region:us",
      "finance"
    ],
    "downloads": 60,
    "likes": 1,
    "cardData": {
      "task_categories": [
        "text-generation"
      ],
      "language": [
        "en"
      ],
      "tags": [
        "finance"
      ],
      "pretty_name": "People from Reddit about Finance",
      "size_categories": [
        "n<1K"
      ]
    },
    "lastModified": "2024-03-11T17:26:31.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": ".gitattributes",
      "size": 2359,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 876,
      "type": "file"
    },
    {
      "path": "merged_data.csv",
      "size": 14901619,
      "type": "file"
    },
    {
      "path": "reddit_HedgeFund.csv",
      "size": 139190,
      "type": "file"
    },
    {
      "path": "reddit_WallStreet.csv",
      "size": 199841,
      "type": "file"
    },
    {
      "path": "reddit_cryptocurrency.csv",
      "size": 1154139,
      "type": "file"
    },
    {
      "path": "reddit_cryptomarkets.csv",
      "size": 1087329,
      "type": "file"
    },
    {
      "path": "reddit_cryptoscams.csv",
      "size": 158092,
      "type": "file"
    },
    {
      "path": "reddit_cryptotechnology.csv",
      "size": 1322626,
      "type": "file"
    },
    {
      "path": "reddit_daytrading.csv",
      "size": 2184195,
      "type": "file"
    },
    {
      "path": "reddit_economiccollapse.csv",
      "size": 483590,
      "type": "file"
    },
    {
      "path": "reddit_economy.csv",
      "size": 3166818,
      "type": "file"
    },
    {
      "path": "reddit_forex.csv",
      "size": 143075,
      "type": "file"
    },
    {
      "path": "reddit_posts.csv",
      "size": 2469444,
      "type": "file"
    },
    {
      "path": "reddit_posts_trading.csv",
      "size": 237152,
      "type": "file"
    },
    {
      "path": "reddit_stocks.csv",
      "size": 2152519,
      "type": "file"
    },
    {
      "path": "seeking_alpha_articles.csv",
      "size": 18,
      "type": "file"
    }
  ],
  "splits": {
    "splits": [
      {
        "dataset": "kowalsky/reddit_about_money",
        "config": "default",
        "split": "train"
      }
    ],
    "pending": [],
    "failed": []
  },
  "first_rows": [
    {
      "config": "default",
      "split": "train",
      "error": 500,
      "body": "{\"error\":\"Column name 'Throw some ads on the page and we'll be happy to click them for you!!\\nI haven\u2019t really checked out the indi yet, but man I like your style.  \\n\\nI can help with your website, maybe convert to TOS, idk other stuff too probably.  Feel free to pm  if you need anything.  You rock"
    }
  ],
  "csv_heads": {
    "merged_data.csv": [
      "Title,Score,URL,Comments,\"It's crazy that I almost thought about monetizing this, rather than giving it for free. It's time to realize and the real flaw of money--it makes people selfish. I want to end that and make people care about each other again. Here is my year long TradingView project, for free. I keep the code tho :)\",601,https://www.reddit.com/r/Trading/comments/lxd6d5/its_crazy_that_i_almost_thought_about_monetizing/,\"Throw some ads on the page and we'll be happy to click them for you!!",
      "I haven\u2019t really checked out the indi yet, but man I like your style.  ",
      "",
      "I can help with your website, maybe convert to TOS, idk other stuff too probably.  Feel free to pm  if you need anything.  You rock.",
      "[deleted]",
      "OMG I love to know that people like you, unselfish and caring for the little people are here and willing to help others with nothing in return than the satisfaction of helping. Thank you so much!\ud83d\udc4c\ud83d\ude4f\ud83d\ude4f"
    ],
    "reddit_HedgeFund.csv": [
      "Title,Score,URL,Comments",
      "\"Tool that tracks flights by executive private jets. Data that hedge funds pay thousands for in order to predict corporate mergers, available to you for free.\",94,https://www.quiverquant.com/sources/corporateflights,\"Thank you.",
      "I love this guy!",
      "This is top level Intel!",
      "Save",
      "I'm new and beginner to this, idk if anyone will read this comment but why is this important? please explain.\""
    ],
    "reddit_WallStreet.csv": [
      "Title,Score,URL,Comments",
      "UPVOTES FOR Nokia Investment,402,https://www.reddit.com/r/wallstreet/comments/l6vvx2/upvotes_for_nokia_investment/,\"I honestly like Nokia! Great Potential for the upside due to the the 1Tb planning in development and the GOV contracts.",
      "[deleted]",
      "Inside in Nok and BB.",
      "Now waiting\ud83e\udd14",
      "This morning, at around 3am cst, NOK was buyable on Robinhood. I get a notification this morning at 8:45 that NOK is now an unsupported stock in Robinhood and that my order of over 30 shares was canceled. Interesting stuff."
    ]
  }
}
```

## README

---
task_categories:
- text-generation
language:
- en
tags:
- finance
pretty_name: People from Reddit about Finance
size_categories:
- n<1K
---
__Description__:

This is an extremely small dataset. I parsed the darkest corners of Reddit to find useful information about finance to build my first NLP model. After teaching the model, I got outputs that made me question my existence and the meaning of life. There is nothing out there this dataset might be useful for, except for building something that should not be built.

__What's Inside__:

It's a mix of finance tips and deep thoughts, all pulled from Reddit's. It's questionable, but sometimes pretty deep.

__Why Use It__:

I actually have no idea. I have spent so much time on parsing, that I cannot just get rid of it.

__Be Careful__:

The dataset is not filtered. So, everybody must understand what could be inside.
