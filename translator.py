from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline


class Translator:
    def __init__(self, model_name, src_lang='arb_Arab', tgt_lang='eng_Latn'):
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.translator = pipeline('translation', model=model, tokenizer=tokenizer,
                                   src_lang=src_lang, tgt_lang=tgt_lang, max_length=400)

    def translate(self, text):
        return self.translator(text)
