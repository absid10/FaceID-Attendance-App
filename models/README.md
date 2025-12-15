# Models

This project does **not** commit trained face-recognition models to git by default.

- The trained LBPH model is written to `models/trainer.yml` at runtime.
- This file may encode biometric information and is typically specific to your local dataset.

## Create / refresh the model
- Run `scripts/01_create_dataset.py` to capture samples
- Run `scripts/02_train_model.py` to train and write `models/trainer.yml`

## Packaged `.exe`
The packaged app writes `models/trainer.yml` next to the executable in a writable folder.
