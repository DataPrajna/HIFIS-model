import os
import argparse
import yaml
import datetime
from tensorflow.keras.models import save_model
from tensorflow.keras.callbacks import EarlyStopping, TensorBoard, Callback
import tensorflow as tf
from azureml.core import Run
from src.train import multi_train, load_dataset
from src.visualization.visualize import plot_roc, plot_confusion_matrix

parser = argparse.ArgumentParser()
parser.add_argument('--preprocessedoutputdir', type=str, help="intermediate preprocessed pipeline data directory")
parser.add_argument('--traininglogsdir', type=str, help="training logs directory")
parser.add_argument('--trainoutputdir', type=str, help="intermediate training pipeline data directory")
args = parser.parse_args()
run = Run.get_context()
print("GPUs available:")
print(tf.config.experimental.list_physical_devices('GPU'))

# Update paths of input data in config to represent paths on blob.
cfg = yaml.full_load(open(os.getcwd() + "./config.yml", 'r'))  # Load config data
cfg['PATHS']['PROCESSED_DATA'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['PROCESSED_DATA'].split('/')[-1]
cfg['PATHS']['PROCESSED_OHE_DATA'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['PROCESSED_OHE_DATA'].split('/')[-1]
cfg['PATHS']['TRAIN_SET'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['TRAIN_SET'].split('/')[-1]
cfg['PATHS']['TEST_SET'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['TEST_SET'].split('/')[-1]
cfg['PATHS']['DATA_INFO'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['DATA_INFO'].split('/')[-1]
cfg['PATHS']['SCALER_COL_TRANSFORMER'] = args.trainoutputdir + '/' + cfg['PATHS']['SCALER_COL_TRANSFORMER'].split('/')[-1]
cfg['PATHS']['MODEL_TO_LOAD'] = args.trainoutputdir + '/' + cfg['PATHS']['MODEL_TO_LOAD'].split('/')[-1]
cfg['PATHS']['LOGS'] = args.traininglogsdir

# Create path for train step output data if it doesn't already exist on the blob
if not os.path.exists(args.trainoutputdir):
    os.makedirs(args.trainoutputdir)

# Load dataset file paths and labels
data = load_dataset(cfg)

# Custom Keras callback that logs all training and validation metrics after each epoch to the current Azure run
class LogRunMetrics(Callback):
    def __init__(self):
        self.model_counter = 0
        super(LogRunMetrics, self).__init__()
    def on_epoch_end(self, epoch, log):
        if epoch == 1:
            self.model_counter += 1
        for metric_name in log:
            run.log('model' + str(self.model_counter) + '_' + metric_name, log[metric_name])

# Set model callbacks
callbacks = [EarlyStopping(monitor='val_loss', verbose=1, patience=cfg['TRAIN']['PATIENCE'], mode='min', restore_best_weights=True),
             LogRunMetrics()]

# Train multiple models and retain references to the best model and its test set metrics
start_time = datetime.datetime.now()
model, test_metrics, best_logs_date = multi_train(cfg, data, callbacks, base_log_dir=cfg['PATHS']['LOGS'])
run.log("TensorBoard logs folder", best_logs_date)
print("TOTAL TRAINING TIME = " + str((datetime.datetime.now() - start_time).total_seconds() / 60.0) + " min")

# Log test set performance metrics, ROC, confusion matrix in Azure run
test_predictions = model.predict(data['X_test'], batch_size=cfg['TRAIN']['BATCH_SIZE'])
for metric_name in test_metrics:
    run.log('test_' + metric_name, test_metrics[metric_name])
roc_plt = plot_roc("Test set", data['Y_test'], test_predictions)
run.log_image("ROC", plot=roc_plt)
cm_plt = plot_confusion_matrix(data['Y_test'], test_predictions)
run.log_image("Confusion matrix", plot=cm_plt)

# Save the model's weights
if cfg['PATHS']['MODEL_WEIGHTS'] is not None:
    save_model(model, cfg['PATHS']['MODEL_TO_LOAD'])  # Save model weights to intermediate blob storage