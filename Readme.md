# Hands-on Language Translation on Low-Resource languages

``Note`` : Everything is implemented from scratch

---

## 📖 Table of Contents  
- [Flow Diagram](#-flow-diagram)  
- [Traditional Supervised Approach](#-traditional-supervised-approach)  
- [Unsupervised Approach](#-unsupervised-approach)  
- [Challenges Faced](#-challenges-faced)
- [References](#-references)

---

## 📊 Flow Diagram

![Language Translation Pipeline](Flow_Diagram.png)

---

## Traditional approach (Supervised Approach): 

This method requires **parallel corpora** (source ↔ target language word pairs).

### Pipeline

1. **Dataset creation Phase**
    - creation of parallel corups: `(src_language, translated_language)`
2. **Vectorization Phase** 
    - Use an embedding model to convert the words -> vectors (embeddings)
3. **Mapping phase**
    - Learn a **transformation matrix** that maps source embeddings to target embeddings (embeddings of target vocab)

### 🧠 Core Idea:
I used **Procrustes Analysis**, a linear mapping technique to align word embeddings from the source language space to the target language space.

> The transformation matrix is learned using **Singular Value Decomposition (SVD)**.

Refer: [`ProcrustesSupervisedAlignment.ipynb`](./Training/ProcrustesSupervisedAlignment.ipynb)

---

## Unsupervised Approach  

Inspired by **GANs (Generative Adversarial Networks)**, this method works **without parallel corpora**.

#### Key Concepts:
- No need for `(src, tar)` word pairs
- Deals with src and tar language independently 

#### Two-Phase Training:

#### **Phase 1: Adversarial Training**
- **Generator** learns to transform source embeddings to appear like target embeddings
- **Discriminator** learns to distinguish between real target embeddings and generated ones
- Both networks are trained simultaneously in a **min-max** fashion

#### **Phase 2: Pseudo Target Word Generation**
- Use the trained Generator to produce `k` nearest target embeddings
- Map these embeddings to actual words using:
  - **K-Nearest Neighbors (KNN)**
  - **Cross-Domain Similarity Local Scaling (CSLS)**

Refer: [`ProcrustesUnSupervisedAlignment.ipynb`](./Training/ProcrustesUnSupervisedAlginment.ipynb)

---

## Challenges Faced : 

One of the major challenge in building an AI model (language/image) is for Indic language is its complexity (Compound words, Character Clusters) and lack of proper tokenizers.

### Language Complexity
- Low-resource languages like Hindi lack well-defined tokenizers and linguistic tools

### Compound Words
- Many Indic words combine in irregular ways, making them difficult to split or process automatically

### Lack of GPU-compatible Preprocessing
- Libraries used for preprocessing (e.g., regular expressions) often **lack GPU support**, slowing down data preparation

### KNN Asymmetry 
- KNN search isn't symmetric: `y` might be in KNN of `x`, but `x` isn't necessarily in KNN of `y` \[1\]
- **Solution**: Use `CSLS` to balance this discrepancy


## 📚 References

1. Conneau, A., Lample, G., Ranzato, M., Denoyer, L., & Jegou, H.  
   **"Word translation without parallel data"**, [arXiv:1710.04087](https://doi.org/10.48550/arXiv.1710.04087), 2017  
2. [**Multilingual Unsupervised and Supervised Embeddings (MUSE)** - Facebook Research](https://github.com/facebookresearch/MUSE)  
3. Zhu, J.-Y., Park, T., Isola, P., & Efros, A. A.  
   **"Unpaired Image-to-Image Translation Using Cycle-Consistent Adversarial Networks"**,  
   *IEEE ICCV 2017*, [DOI: 10.1109/ICCV.2017.244](https://doi.org/10.1109/ICCV.2017.244)