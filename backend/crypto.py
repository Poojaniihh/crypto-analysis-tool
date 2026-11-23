import json
import os
from json import JSONDecodeError
from typing import List

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import ValidationError
from starlette.exceptions import HTTPException

from model import CryptoAnalysisRequest, CryptoAnalysisResponse, CryptoCompareRequest, CryptoComparisonResponse
from fastapi.middleware.cors import CORSMiddleware



load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_URL = os.getenv("OPENROUTER_URL")
COINGECKO_URL = os.getenv("COINGECKO_URL")

app = FastAPI(title="Crypto Analysis AI Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # or specify your frontend URL like "http://localhost:5500"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_crypto_insights(coin_list: List[str]):

    params = {
        "ids" : ",".join(coin_list),
        "vs_currency" : "usd"
    }

    resp = requests.get(COINGECKO_URL, params=params)

    return resp.json()


SYSTEM_PROMPT_COMPARE = """
You are a "CryptoAnalyst AI" - a professional crypto market analyst.

You will be given recent market for data for several crypto currencies (price, market cap, volume, 24h change)

Your job is to compare these coins and determine which one currently show stronger market potential with a valid JSON schema

CRITICAL INSTRUCTIONS:
- You must output *only valid json* , not inside quote, not inside markdowns, not as a string.
- DO not include ``` json or ``` anywhere
- Do not add explanation, greeting, or text before or after the JSON 
- The JSON must begin directly with { and end with }


Rules:
- Return one Analysis per coin
- Follow the exact JSON schema:

{
"comparison" : {
                  "winner": <coin name with strongest outlook>,
                  "summary": <1-2 sentence human-style summary of why>
                  "reasons" : List
                  "<reason 1>",
                  "<reason 2>",
                  "<reason 3>"
}

- Provide 3 key_reasons and 3 insights
- Base your reasoning on give metrics (e.g, price change %, market cap trends).
- Always output only JSON - no Markdown, no Explanation
"""

SYSTEM_PROMPT_ANALYSIS = """
You are a "CryptoAnalyst AI" - a professional crypto market analyst.

You will be given recent market for data for several crypto currencies (price, market cap, volume, 24h change)

Your job is to produce a structured analysis with a valid JSON schema

CRITICAL INSTRUCTIONS:
- You must output *only valid json* , not inside quote, not inside markdowns, not as a string.
- DO not include ``` json or ``` anywhere
- Do not add explanation, greeting, or text before or after the JSON 
- The JSON must begin directly with { and end with }


Rules:
- Return one Analysis per coin
- Follow the exact JSON schema:
{
"analysis" : [
        {
        "coin" : "<coin name>",
        "summary" : "<2-3 line summary>",
        "sentiment" : "bullish" | "neutral" | "bearish",
        "key_factors" : [
        { "factor" : "<factor name>" , "impact": "<impact details>" }
        ],
        "insights" : [
        {"prediction" : "<short-term prediction>" , "confidence" : <0-100>}
        ]
        }
]
}
- Provide 3 key_factors and 3 insights per coin
- Base your reasoning on give metrics (e.g, price change %, market cap trends).
- Always output only JSON - no Markdown, no Explanation

"""


def call_openrouter_api(market_data, system_prompt, request_type: str = "analyze"):
    header = {
        "Authorization" : f"Bearer {OPENROUTER_KEY}",
        "Content-Type" : "application/json"
    }

    body = {
        "model" : "meta-llama/llama-3.3-70b-instruct:free",
        "messages" : [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the market data - {json.dumps(market_data, indent=2)}"}
        ]
    }

    llm_response = requests.post(OPENROUTER_URL, json=body, headers=header)
    json_str = llm_response.json()["choices"][0]["message"]["content"]


    try:
        payload = json.loads(json_str)
    except JSONDecodeError as e:
        raise HTTPException(status_code=502, detail="LLM did not return a valid JSON")
    try:
        if request_type == "analyze":
            return CryptoAnalysisResponse.model_validate(payload)
        else:
            return CryptoComparisonResponse.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=502, detail=f"LLM Json validation failed -- {str(e)}")


@app.post("/crypto/analyze")
def crypto_analysis(request: CryptoAnalysisRequest):

    crypto_data = get_crypto_insights(request.coins)
    market_data = [{
        "name" : data["name"],
        "symbol" : data["symbol"],
        "current_price" : data["current_price"],
        "market_cap" : data["market_cap"],
        "total_volume" : data["total_volume"],
        "price_change_percentage_24h" : data["price_change_percentage_24h"]
    } for data in crypto_data]

    return call_openrouter_api(market_data, system_prompt=SYSTEM_PROMPT_ANALYSIS, request_type="analyze")

@app.post("/crypto/compare")
def crypto_compare(request: CryptoCompareRequest):
    crypto_data = get_crypto_insights(request.coins)
    market_data = [{
        "name": data["name"],
        "symbol": data["symbol"],
        "current_price": data["current_price"],
        "market_cap": data["market_cap"],
        "total_volume": data["total_volume"],
        "price_change_percentage_24h": data["price_change_percentage_24h"]
    } for data in crypto_data]

    return call_openrouter_api(market_data, system_prompt=SYSTEM_PROMPT_COMPARE, request_type="compare")



# if __name__ == '__main__':
#     get_crypto_insights(["bitcoin" , "ethereum"])



