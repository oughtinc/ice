# Interactive Composition Explorer 🧊

ICE is a Python library and trace visualizer for language model programs.

## Screenshot

<p align="center">
  <img alt="ice-screenshot" src="https://user-images.githubusercontent.com/382515/192681645-6ed87072-2dc6-4982-92d1-8de209bc3ef6.png" />
  Execution trace visualized in ICE
</p>

## Features

- Run language model recipes in different modes: humans, human+LM, LM
- [Inspect the execution traces in your browser for debugging](https://github.com/oughtinc/ice/wiki/ICE-UI-guide)
- Define and use new language model agents, e.g. chain-of-thought agents
- Run recipes quickly by parallelizing language model calls
- Reuse component recipes such as question-answering, ranking, and verification

## ICE is pre-1.0

:warning: **The ICE API may change at any point.** The ICE interface is being actively developed and we may change the API at any point, including removing functionality, renaming methods, splitting ICE into multiple projects, and other similarly disruptive changes. Use at your own risk.

## Requirements

ICE requires Python 3.10. If you only have newer or older version(s) of Python installed, we recommend using [pyenv](https://github.com/pyenv/pyenv) to install Python 3.10 and manage multiple Python versions.

If you use Windows, you'll need to run ICE inside of [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).

## Getting started

1. As part of general good Python practice, consider first creating and activating a [virtual environment](https://docs.python.org/3/library/venv.html) to avoid installing ICE 'globally'. For example:

   ```shell
   python3.10 -m venv venv
   source venv/bin/activate
   ```

1. Install ICE:

   ```shell
   pip install ought-ice
   ```

1. Set required secrets in `~/.ought-ice/.env`. See [`.env.example`](https://github.com/oughtinc/ice/blob/main/.env.example) for the format.

1. To learn more, go through [the Primer](https://primer.ought.org/).

## Developing ICE

1. If you want to make changes to ICE itself, clone the repository, then install it in editable mode:

   ```shell
   python3.10 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -e '.[dev]' --config-settings editable_mode=compat
   pre-commit install
   npm --prefix ui ci
   npm --prefix ui run dev
   ```

2. If you're working on the backend, you might find it helpful to remove the cache of language model calls:

   ```shell
   rm -r ~/.ought-ice/cache
   ```

3. `pre-commit` complains if your code doesn't pass certain checks. It runs when you commit, and will possibly reject your commit and make you have to fix the problem(s) before you can commit again. (So you should probably use the same commit message you used the first time.)

Note that you don't technically _need_ to run `pre-commit install`, but _not_ doing so may cause your commits to fail CI. (Which can be noisy, including by generating commits that will e.g. fix formatting.)

4. To run the tests:

   ```shell
   pytest
   ```

Also, since some tests are relatively slow, you might want to run the ever-useful `pytest -k` option to run only the tests you're interested in. For example, to run only the tests in `test_json.py`:

```shell
pytest -k test_json
```

5. Manual testing

You can test that some canonical recipes work with the following. **Be careful!** `rm -rf ~/.ought-ice/traces` will **delete all your traces**.

```
rm -rf ~/.ought-ice/traces
pytest
python -m ice.server start
```

Then look at the trace IDs in `~/.ought-ice/traces` and visit the corresponding URLs in your browser. (E.g. `http://localhost:8935/traces/$TRACE_ID`.) I **strongly recommend** against opening all the traces in this directory automatically because the visual effect of rapidly opening so many tabs (with a white background?) mimics a strobelight, which could be [dangerous](https://www.pennmedicine.org/updates/blogs/neuroscience-blog/2019/august/surprising-epilepsy-seizure-triggers).

Note that `pytest` can take a while to run :)

## Terminology

- **Recipes** are decompositions of a task into subtasks.

  The meaning of a recipe is: If a human executed these steps and did a good job at each workspace in isolation, the overall answer would be good. This decomposition may be informed by what we think ML can do at this point, but the recipe itself (as an abstraction) doesn’t know about specific agents.

- **Agents** perform atomic subtasks of predefined shapes, like completion, scoring, or classification.

  Agents don't know which recipe is calling them. Agents don’t maintain state between subtasks. Agents generally try to complete all subtasks they're asked to complete (however badly), but some will not have implementations for certain task types.

- The **mode** in which a recipe runs is a global setting that can affect every agent call. For instance, whether to use humans or agents. Recipes can also run with certain `RecipeSettings`, which can map a task type to a specific `agent_name`, which can modify which agent is used for that specific type of task.

## Additional resources

1. [Join the ICE Slack channel](https://join.slack.com/t/ice-1mh7029/shared_invite/zt-1h8118i28-tPDSulG8C~4dr5ZdAky1gg) to collaborate with other people composing language model tasks. You can also use it to ask questions about using ICE.

2. [Watch the recording of Ought's Lab Meeting](https://www.youtube.com/watch?v=cZqq4muY5_w) to understand the high-level goals for ICE, how it interacts with Ought's other work, and how it contributes to alignment research.

3. [Read the ICE announcement post](https://ought.org/updates/2022-10-06-ice-primer) for another introduction.

## Contributions

ICE is an [open-source](https://github.com/oughtinc/ice/blob/main/LICENSE.md) project by [Ought](https://ought.org/). We're an applied ML lab building the AI research assistant [Elicit](https://elicit.org/).

We welcome community contributions:

- If you're a developer, you can dive into the codebase and help us fix bugs, improve code quality and performance, or add new features.
- If you're a language model researcher, you can help us add new agents or improve existing ones, and refine or create new recipes and recipe components.

For larger contributions, make an issue for discussion before submitting a PR.

And for even larger contributions, join us - [we're hiring](https://ought.org/careers)!

## How to cite

If you use ICE, please cite:

> [Iterated Decomposition: Improving Science Q&A by Supervising Reasoning Processes](https://arxiv.org/abs/2301.01751). Justin Reppert, Ben Rachbach, Charlie George, Luke Stebbing Jungwon Byun, Maggie Appleton, Andreas Stuhlmüller (2023). Ought Technical Report. arXiv:2301.01751 [cs.CL]

Bibtex:

```bibtex
@article{reppert2023iterated,
  author = {Justin Reppert and Ben Rachbach and Charlie George and Luke Stebbing and Jungwon Byun and Maggie Appleton and Andreas Stuhlm\"{u}ller},
  archivePrefix = {arXiv},
  eprint = {2301.01751},
  primaryClass = {cs.CL},
  title = {Iterated Decomposition: Improving Science Q&A by Supervising Reasoning Processes},
  year = 2023,
  keywords = {language models, decomposition, workflow, debugging},
  url = {https://arxiv.org/abs/2301.01751}
}
```
