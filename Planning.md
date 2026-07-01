# AI201 Project #4 - Provenance Guard
Provenance Guard is an API endpoint that accepts a piece of text-based content (a poem, a short story excerpt, a blog post) and classifies whether they are AI or human-made

## Detection Signals
I will be incorporating 2 signals for text detection:
1. LLM-based classification (Groq): it'll ask the model to assess whether text reads as human or AI-generated. Captures semantic and stylistic coherence holistically. This signal will output a binary flag (human vs AI)
2. Stylometric heuristics: Measures statistical properties in terms of proportion that differ between human and AI writing — sentence length variance, type-token ratio (vocabulary diversity), punctuation density. For instance, AI text tends to be more uniform; human writing is more variable. This signal will output a series of values ranging in proportions to numerical values corresponding to each of the three metrics they evaluate

UPDATE: Type-token ratio performs poorly at shorter responses, so I will be swapping this with average sentence complexity. 

I'll combine these two detection signals into a confidence score through majority vote. Essentially, each signal will vote on a label, and the confidence score will be the proportion of votes for human label. 

## Uncertainty Representation
A confidence score of 0.6 means uncertain in my system. I will combinae the raw signal outputs to a calibrated score as mentioned in Detection Score through majority vote based on proportion of voted labels for "likely human". Since the API endpoint will be classifying each text into three labels: 
    "likely AI", "uncertain", and "likely human", the following threshold is as indicated:
    
    1. Likely AI: 0.0 - 0.4
    2. Uncertain: 0.41 - 0.6
    3. Likely Human: 0.61 - 1.0
    
## Transparency Label Design
For a high confidence AI result, the label will state as follows:
"This text is likely to be written by AI"

For a high confidence human result, the label will state as follows:
"This text is likely to be written by human"

For uncertain result, the label will state as follows:
"I am unable to determine whether this text is written by a human or an AI."

## Appeals Workflow
Users can submit an appeal providing the text. The system updates the status to "Under Review", log the appeal alongisde the original classification decision in the audit log, and returns a confirmation to the user that the appeal was received. 


## Anticipated Edge Cases
My system might handle the following poorly:
1. Formal literature: Formal essays or responses have textual patterns similar to Ai-generated text. 
2. Poems with heavy use of repetition and simple vocabulary

## Architecture
Submission Flow                                         Appeal Flow
    │                                                       |
    ▼                                                       ▼ 
POST / submit                                           Post / Appeal
    │                                                       |
    ▼                                                       ▼ 
LLM Based Classification Signal (Groq)                  Status Update
    │                                                       |
    ▼                                                       |
Stylometric Heuristics Signal in Python                     |
    │                                                       |
    ▼                                                       |
Confidence Scoring                                          |
    │                                                       |
    ▼                                                       |
Transparency Label                                          |
    │                                                       |
    ▼                                                       |
Audit Log ◀--------------------------------------------------
    │
    ▼
Response    

There are two main flows in this system: Submission and Appeal flow. 
Users can submit their text to be assessed by two signals for label attribution, or
if they've done so already and found errors in the system's judgement, they can
submit an appeal with their text and correct attribution. Both the label from
submission and status update enters into audit log and outputs a response. 

## AI Tool Plan
I'll be using AI to implement these pipelines as demonstrated in the architecture. 

For my third checkpoint, which includes the implementation of the submission endpoint and first signal, I'll provide Claude my detection signals section and the architecture diagram to generate the Flash app skeleton and the LLM based function. I'll verify the output with several test cases with few inputs before wiring into the endpoint. 

For my fourth checkpoint, which includes the implementation of the second signal and confidence scoring, I'll provide Claude my specs on detection signals, uncertainty representation and architecture diagram to generate the second signal functon and scoring logic. I'll then verify whether the scores vary meaningful between clearly AI and clearly human text.

For my fifth checkpoint, which includes the implementation of the production layer, I'll provide Claude my label variants, appeals workflow and architecture diagram to generate the label generation logic and appeal enpoint. I'll verify by testing all three label variants are reachable and that an appeal updates status correctly. 

## Test Inputs

1. AI
curl -s -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{"text": "In 2026, the deepening \"K-shaped\" economy signifies a growing disparity where high-income households contribute significantly to economic growth, benefiting from rising assets and investments, while lower-income groups face economic contraction, limited job opportunities, and widening income inequality, potentially leading to increased social and economic divides.", "creator_id": "u1"}'

2. Human
curl -s -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{"text": "Ive seen people already watching it on Prime or Apple TV. I wanna watch it today but is just not available here in Mexico. Ive seen people struggling from other countries. Have anyone managed to see it with a VPN or some other place?", "creator_id": "u2"}'

3. Human
curl -s -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{"text": "I backpacked in western Euripe for a few weeks when I was 20. It was fun. I stayed at youth hostels. At the time I was going to university in London and we were on spring break. My friend ran out of money during our first stop in Amsterdam. I figured I could always go back to London if I felt that I needed to. Instead I kept meeting travel companions at new hostels that I could spend time with and often we went to the next country together. I met lots of people my age from all over the world.", "creator_id": "u2"}'

4. Human (formal writing from 2018)
curl -s -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{"text": "In 2018 companies continue to look for ways to cut through the noise, create mindshare, and establish themselves and both experts and influencers. AI-driven marketing, social targeting, and general content marketing are the predominant solution for most, but the biggest shift right now is in the channels being used to distribute this thought leadership.", "creator_id": "u3"}'

5. AI
curl -s -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{"text": "Classification: Fish belong to the phylum Chordata and represent a paraphyletic group, meaning they include various evolutionary lines but exclude their tetrapod descendants (amphibians, reptiles, birds, and mammals).", "creator_id": "u4"}'

Appeal: #4 Content Id
curl -s -X POST http://127.0.0.1:5001/appeal -H "Content-Type: application/json" -d '{"content_id": "db10f010-6c43-4687-b8b2-a1988d414dd5", "creator_reasoning": "It was written in Forbes back in 2018 when LLMs and NLPs weren'\''t well-known."}' | python -m json.tool

## Rate Limiting Testing
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:5001/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done
