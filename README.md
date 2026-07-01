# AI201 Project #4 - Provenance Guard
Provenance Guard is an API endpoint that accepts a piece of text-based content (a poem, a short story excerpt, a blog post) and classifies whether they are AI or human-made

## Detection Signals
I will be incorporating 2 signals for text detection:
1. LLM-based classification (Groq): it'll ask the model to assess whether text reads as human or AI-generated. Captures semantic and stylistic coherence holistically. This signal will output a binary flag (human vs AI)
2. Stylometric heuristics: Measures statistical properties in terms of proportion that differ between human and AI writing — sentence length variance, type-token ratio (vocabulary diversity), punctuation density. For instance, AI text tends to be more uniform; human writing is more variable. This signal will output a series of values ranging in proportions to numerical values corresponding to each of the three metrics they evaluate

UPDATE: Type-token ratio performs poorly at shorter responses, so I will be swapping this with average sentence complexity. 

### Anticipated Edge Cases
My system might handle the following poorly:
1. Formal literature: Formal essays or responses have textual patterns similar to Ai-generated text. 
2. Poems with heavy use of repetition and simple vocabulary

## Confidence Scoring

I'll combine these two detection signals into a confidence score through majority vote. Essentially, each signal will vote on a label, and the confidence score will be the proportion of votes for human label. 

### Threshold and Uncertainty Representation
A confidence score of 0.6 means uncertain in my system. I will combinae the raw signal outputs to a calibrated score as mentioned in Detection Score through majority vote based on proportion of voted labels for "likely human". Since the API endpoint will be classifying each text into three labels: 
    "likely AI", "uncertain", and "likely human", the following threshold is as indicated:
    
    1. Likely AI: 0.0 - 0.4
    2. Uncertain: 0.41 - 0.6
    3. Likely Human: 0.61 - 1.0


### Examples
Example #1: "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won'\''t go back unless someone drags me there."

Audit Log Results:
{
  "attribution": "likely_human",
  "confidence": 1.0,
  "content_id": "4124e9c7-fe0f-4312-953a-b9d838b27111",
  "creator_id": "u3",
  "label": "This text is likely to be written by human",
  ...
}

Example #2: "Russian President Vladimir Putin has publicly acknowledged that Ukrainian long-range strikes are creating fuel supply problems inside Russia, as videos obtained by Fox News Digital show long lines, angry motorists and fights erupting at filling stations across several Russian regions."

Audit Log Results:
{
  "attribution": "uncertain",
  "confidence": 0.5,
  "content_id": "5b998875-9929-4e2c-ada2-18b1bf360055",
  "creator_id": "u3",
  "label": "I am unable to determine whether this text is written by a human or an AI."
  ...
}



## Transparency Label Design
For a high confidence AI result, the label will state as follows:
"This text is likely to be written by AI"

Example:
Text: "In 2026, the deepening "K-shaped" economy signifies a growing disparity where high-income households contribute significantly to economic growth, benefiting from rising assets and investments, while lower-income groups face economic contraction, limited job opportunities, and widening income inequality, potentially leading to increased social and economic divides."

Audit Log:
{
  "attribution": "likely_ai",
  "confidence": 0.0,
  "content_id": "77db2483-0c40-4d70-af32-23808e29536c",
  "creator_id": "u1",
  "label": "This text is likely to be written by AI",
  ...
}


For a high confidence human result, the label will state as follows:
"This text is likely to be written by human"

Example:
Text: "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won'\''t go back unless someone drags me there."

Audit Log Results:
{
  "attribution": "likely_human",
  "confidence": 1.0,
  "content_id": "4124e9c7-fe0f-4312-953a-b9d838b27111",
  "creator_id": "u3",
  "label": "This text is likely to be written by human",
  ...
}


For uncertain result, the label will state as follows:
"I am unable to determine whether this text is written by a human or an AI."

Example:
Text: "Russian President Vladimir Putin has publicly acknowledged that Ukrainian long-range strikes are creating fuel supply problems inside Russia, as videos obtained by Fox News Digital show long lines, angry motorists and fights erupting at filling stations across several Russian regions."

Audit Log Results:
{
  "attribution": "uncertain",
  "confidence": 0.5,
  "content_id": "5b998875-9929-4e2c-ada2-18b1bf360055",
  "creator_id": "u3",
  "label": "I am unable to determine whether this text is written by a human or an AI."
  ...
}

## Appeals Workflow
Users can submit an appeal providing the text. The system updates the status to "Under Review", log the appeal alongisde the original classification decision in the audit log, and returns a confirmation to the user that the appeal was received. 

## Rate Limiting
I chose to implemenent a rate limiting of 10 per min, as per common standards I researched online.

Here's an instance of what occurs:

"
127.0.0.1 - - [30/Jun/2026 18:32:36] "POST /appeal HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:16] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:16] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:17] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:17] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:18] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:18] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:19] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:19] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:25] "POST /submit HTTP/1.1" 200 -

127.0.0.1 - - [30/Jun/2026 18:41:26] "POST /submit HTTP/1.1" 429 -

127.0.0.1 - - [30/Jun/2026 18:41:26] "POST /submit HTTP/1.1" 429 -

"

## Limitations
Very brief responses such as one-sentencers are almost guaranteed to be classified as human. This is likely due to both signals not having enough information to semantically and structurally assess whether an AI or human wrote it. 

## Spec Reflection
Writing up the specs allowed me to save time during implementation and focus more testing and ensuring that each component works as intended and as accurately as possible. One way that the implementation divulged from my specs write-up was replacing type-token ratio metric with average sentence complexity. During my testing with stylometric signals, I realized that majority of the responses were classified as human-made due to high type-token ratio given my response length on average are considerably short. As such, I replaced it with average sentence complexity to better detect AI. This allowed the system to recognized more AI responses correctly 

## AI Usage Section
I directed Claude to build the pipelines for the system. 
1. I shared Claude my specs write up for stylometric heuristic signal and architectural diagram to build up the stylometric heuristic. During testing, I decided to override its weighting decisions as I realized average sentence complexity is more relevant towards better classification compared to other metrics. This is due to many of my test cases being of smaller responses. I think if my test cases were of much longer length, I'd equally weigh the metrics. 

2. I shared Claude my specs write up for LLM classification signal and architectural diagram to build up the Groq signal. I advised Claude with specific details on how the signal should be build, from how it should assess the text to what its output entail. I revised how the API should be accessed as initially, the implementation did not include it. 

