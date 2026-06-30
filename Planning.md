# AI201 Project #4 - Provenance Guard
Provenance Guard is an API endpoint that accepts a piece of text-based content (a poem, a short story excerpt, a blog post) and classifies whether they are AI or human-made

## Detection Signals
I will be incorporating 2 signals for text detection:
1. LLM-based classification (Groq): it'll ask the model to assess whether text reads as human or AI-generated. Captures semantic and stylistic coherence holistically. This signal will output a binary flag (human vs AI)
2. Stylometric heuristics: Measures statistical properties in terms of proportion that differ between human and AI writing — sentence length variance, type-token ratio (vocabulary diversity), punctuation density, or average sentence complexity. For instance, AI text tends to be more uniform; human writing is more variable. This signal will output a series of values ranging in proportions to numerical values corresponding to each of the three metrics they evaluate

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
2. Poems with heavy use of repetition and simple vocabulry

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




