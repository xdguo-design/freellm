import json
from pathlib import Path


def test_ling_31_free_registration_link_is_the_model_specific_vercel_page():
    offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
    offer = next(item for item in offers if item.get("id") == "ant-ling-3-1-flash-free")

    assert offer["register"] == "https://vercel.com/ai-gateway/models/ling-3.1-flash-free"
    assert offer["registerLabel"] == "模型注册页"
    assert offer["registerLabelEn"] == "Model registration page"
    assert ["Vercel 模型页", "https://vercel.com/ai-gateway/models/ling-3.1-flash-free"] in offer["links"]
