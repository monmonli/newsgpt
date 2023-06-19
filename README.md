# LowBing Project

This repository contains a Python-Flask server that communicates with Vue.js front end to fetch news and answer to user prompt.

## Getting Started

- Install server dependencies.

```
cd api
pip3 install -r requirements.txt
python3 -m flask run --host=0.0.0.0 --port=5137

```

- Install client dependencies.

```
cd lowbing
npm run dev
```

The client will start and can be accessed at http://127.0.0.1:5173/.

## Demo

- [Chinese version input](https://github.com/monmonli/lowbing/assets/79496995/b280fc2a-63f2-4f3e-9c22-4fee35d99e96)
- [English version input](https://github.com/monmonli/lowbing/assets/79496995/389ff3cd-1891-440e-bf8e-7fed2904c842)

## Cite

- Code adapted from the NewsGPT GitHub repository by Parsa Ghaffari (https://github.com/parsaghaffari/newsgpt).
