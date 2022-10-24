### Evaluate a paragraph synthesis recipe

1. Set is as the RECIPE_TO_RUN in ./eval_synthesize.py
2. Run ./eval_synthesize.py, e.g. `docker compose exec ice python ice/recipes/paragraph_synthesis/eval_synthesize.py`
3. The results will be in ice/data, e.g. `ice/data/synthesize_compositional_from_df_eval.csv`. Upload them to Google Sheets
4. Add your ratings to that sheet
5. You can then summarize the ratings using a combo of:
   1. https://github.com/oughtinc/human_data/blob/main/human_data/projects/paragraph_synthesis_ft/notebooks/report_on_eval.ipynb
   2. scripts/summarize-experiment-evals.sh <path to a CSV containing your ratings>
