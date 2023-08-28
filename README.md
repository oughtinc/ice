# Interactive Composition Explorer 🧊

ICE is a Python library and trace visualizer for language model programs.

## Screenshot

<p align="center">
  <img alt="ice-screenshot" src="https://user-images.githubusercontent.com/382515/192681645-6ed87072-2dc6-4982-92d1-8de209bc3ef6.png" />
  Execution trace visualized in ICE
</p>

## Datasets

[Ethics](https://github.com/LLM-Ethics/EthicsSuite)

[Moral Choice](https://t.co/FfQyLGGwiq)

[Colaboratory](https://colab.research.google.com/drive/1roLQgXhEtI83Q5vX1q24Q9iDgu5LFFWA?usp=sharing#scrollTo=9524934a-5241-4bb2-b74f-821a4883e2e0)



## Features

- Run language model recipes in different modes: humans, human+LM, LM
- [Inspect the execution traces in your browser for debugging](https://github.com/oughtinc/ice/wiki/ICE-UI-guide)
- Define and use new language model agents, e.g. chain-of-thought agents
- Run recipes quickly by parallelizing language model calls
- Reuse component recipes such as question-answering, ranking, and verification

## ICE is pre-1.0

:warning: **The ICE API may change at any point.** The ICE interface is being actively developed and we may change the API at any point, including removing functionality, renaming methods, splitting ICE into multiple projects, and other similarly disruptive changes. Use at your own risk.

## Requirements

ICE requires Python 3.9, 3.10, or 3.11. If you don't have a supported version of Python installed, we recommend using [pyenv](https://github.com/pyenv/pyenv) to install a supported Python version and manage multiple Python versions.

If you use Windows, you'll need to run ICE inside of [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).

## Getting started

1. As part of general good Python practice, consider first creating and activating a [virtual environment](https://docs.python.org/3/library/venv.html) to avoid installing ICE 'globally'. For example:

   ```shell
   python -m venv venv
   source venv/bin/activate
   ```

1. Install ICE:

   ```shell
   pip install ought-ice
   ```

1. Run the Hello World recipe in [the Primer](https://primer.ought.org/) to see the trace rendered.

1. Optionally, set secrets (like your OpenAI API key) in `~/.ought-ice/.env`. See [`.env.example`](https://github.com/oughtinc/ice/blob/main/.env.example) for the format. If these are not set, you'll be prompted for them when you run recipes that need them.

## Developing ICE

1. If you want to make changes to ICE itself, clone the repository, then install it in editable mode:

   ```shell
   python -m venv venv
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

### Storybook

We use [Storybook](https://storybook.js.org/) for UI tests. You can run them locally:

```shell
npm --prefix ui run storybook
```

Note that `build-storybook` is only for CI and shouldn't be run locally.

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
