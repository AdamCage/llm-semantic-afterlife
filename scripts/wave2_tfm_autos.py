import transformers

print("version", transformers.__version__)
names = [n for n in dir(transformers) if "AutoModel" in n or "Mistral3" in n or "Ministral" in n or "Gemma4" in n]
print("names", names)
for n in (
    "AutoModelForCausalLM",
    "AutoModelForConditionalGeneration",
    "AutoModelForImageTextToText",
    "Mistral3ForConditionalGeneration",
    "Gemma4UnifiedForConditionalGeneration",
):
    print(n, hasattr(transformers, n))
