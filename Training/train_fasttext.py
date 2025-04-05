import fasttext

if __name__=="__main__":
    
    vocab_limit = 10000

    print(f"Training fast text on custom hindi dataset")
    model_hi = fasttext.train_unsupervised(r"TrainingReadyHindiText.txt")

    print(f"Training fast text on custom english dataset")
    model_en = fasttext.train_unsupervised(r"TrainingReadyEnglishText.txt")

    model_hi.save_model("custom_models/model_hi.bin")
    model_en.save_model("custom_models/model_en.bin")