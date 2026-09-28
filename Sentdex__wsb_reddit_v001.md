# Sentdex/wsb_reddit_v001 (dataset)

```json
{
  "kind": "dataset",
  "id": "Sentdex/wsb_reddit_v001",
  "url": "https://huggingface.co/datasets/Sentdex/wsb_reddit_v001",
  "meta": {
    "tags": [
      "license:apache-2.0",
      "size_categories:100K<n<1M",
      "format:json",
      "modality:text",
      "library:datasets",
      "library:pandas",
      "library:mlcroissant",
      "library:polars",
      "region:us"
    ],
    "downloads": 54,
    "likes": 5,
    "cardData": {
      "license": "apache-2.0"
    },
    "lastModified": "2023-08-25T17:56:31.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": ".gitattributes",
      "size": 2357,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 372,
      "type": "file"
    },
    {
      "path": "wsb-v001.json",
      "size": 25709257,
      "type": "file"
    }
  ],
  "splits": {
    "splits": [
      {
        "dataset": "Sentdex/wsb_reddit_v001",
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
      "features": [
        {
          "feature_idx": 0,
          "name": "sample",
          "type": {
            "dtype": "string",
            "_type": "Value"
          }
        }
      ],
      "rows": [
        {
          "sample": "[INST]\nYup. Insane payments. Not sustainable. But the banks are all in\n[/INST]\n\nBut what if they only give loans to unemployed people? That way, the banks wouldn't have any risk, since 6 x 0 is 0."
        },
        {
          "sample": "[INST]\nDid the run out of water there yet?\n[/INST]\n\nIIRC they have in Cape Town"
        },
        {
          "sample": "[INST]\nThats the same thing? \n  \n Edit: learned the difference\n[/INST]\n\n^ This guy doesn't get the joke."
        },
        {
          "sample": "[INST]\nOriginally it wasn't. I marked it using my secret mod powers.\n[/INST]\n\nNice"
        },
        {
          "sample": "[INST]\nPembrolizumab is the single defining factor of Merck right now. The entirety of stock movement is based around this single immunotherapy. \n  \n If pembrolizumab can consistently continue to show that it is a better PD-1 checkpoint inhibitor over competitors, which so far, it generally has managed to do, Merck will continue to do well.\n[/INST]\n\nYea Keytruda is really important for them, but it's kind of disappointing that they don't have multiple irons in the fire currently."
        }
      ]
    }
  ]
}
```

## README

---
license: apache-2.0
---

This is Approximately 2017ish to 2018ish /r/wallstreetbets subreddit comment/reply data that had at least a few upvotes. Other than filtering for parent/reply pairs and a minimum threshold of votes (5), no effort has been made on this version to improve the quality of the dataset. Will possibly try to improve the quality in future versions. 
