import os
import yaml
import argparse
import datetime
from src.data.preprocess import preprocess

parser = argparse.ArgumentParser()
parser.add_argument('--rawdatadir', type=str, help="Raw HIFIS client data directory")
parser.add_argument('--preprocessedoutputdir', type=str, help="intermediate pipeline data")
args = parser.parse_args()
cur_date = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

# Modify paths in config file based the Azure datastore paths passed as arguments.
cfg = yaml.full_load(open(os.getcwd() + "./config.yml", 'r'))  # Load config data
cfg['PATHS']['RAW_DATA'] = args.rawdatadir + '/' + cfg['PATHS']['RAW_DATA'].split('/')[-1]
cfg['PATHS']['RAW_SPDAT_DATA'] = args.rawdatadir + '/' + cfg['PATHS']['RAW_SPDAT_DATA'].split('/')[-1]
cfg['PATHS']['PROCESSED_DATA'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['PROCESSED_DATA'].split('/')[-1]
cfg['PATHS']['PROCESSED_OHE_DATA'] = args.preprocessedoutputdir+ '/' + cfg['PATHS']['PROCESSED_OHE_DATA'].split('/')[-1]
cfg['PATHS']['TRAIN_SET'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['TRAIN_SET'].split('/')[-1]
cfg['PATHS']['TEST_SET'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['TEST_SET'].split('/')[-1]
cfg['PATHS']['GROUND_TRUTH'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['GROUND_TRUTH'].split('/')[-1]
cfg['PATHS']['DATA_INFO'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['DATA_INFO'].split('/')[-1]
cfg['PATHS']['ORDINAL_COL_TRANSFORMER'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['ORDINAL_COL_TRANSFORMER'].split('/')[-1]
cfg['PATHS']['OHE_COL_TRANSFORMER_MV'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['OHE_COL_TRANSFORMER_MV'].split('/')[-1]
cfg['PATHS']['OHE_COL_TRANSFORMER_SV'] = args.preprocessedoutputdir + '/' + cfg['PATHS']['OHE_COL_TRANSFORMER_SV'].split('/')[-1]

# Create path for preproces step output data if it doesn't already exist on the blob
if not os.path.exists(args.preprocessedoutputdir):
    os.makedirs(args.preprocessedoutputdir)

# Run preprocessing.
preprocessed_data = preprocess(config=cfg, n_weeks=None, include_gt=True, calculate_gt=True,
                               classify_cat_feats=True, load_ct=False)