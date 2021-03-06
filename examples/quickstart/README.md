# Get up and running quickly
This is the quickstart example that runs a `TrainingPipeline` to train a Tensorflow-based classifier on the 
[Pime Indian Diabetes dataset](https://www.kaggle.com/uciml/pima-indians-diabetes-database).

### Pre-requisites
In order to run this example, you need to clone the zenml repo.

```bash
git clone https://github.com/maiot-io/zenml.git
```

Before continuing, either [install the zenml pip package](https://docs.zenml.io/getting-started/installation.html) or install it [from the cloned repo](../../zenml/README.md). 

```
cd zenml
zenml init
cd examples/quickstart
```

### Run the project
Now we're ready. Execute:

```bash
python quickstart.py
```

Or just a jupyter notebook
```bash
jupyter notebook  # jupyter must be installed
```


### Clean up
In order to clean up, in the root of your repo, delete the remaining zenml references.

```python
cd ../..
rm -r .zenml
rm -r pipelines
```

## Next Steps
Try some of the other examples including using [PyTorch](../pytorch), [custom Backends](../backends), or [distributed processing](../gcp_dataflow_processing)!