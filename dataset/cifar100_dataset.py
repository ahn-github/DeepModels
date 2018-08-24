from urllib.request import urlretrieve
from os.path import isfile, isdir

from tqdm import tqdm
import tarfile
import pickle
import numpy as np

import skimage
import skimage.io
import skimage.transform

from dataset.dataset import Dataset
from dataset.dataset import DownloadProgress

class Cifar100(Dataset):
    def __init__(self):
        Dataset.__init__(self, name='Cifar-100', path='cifar-100-python',  num_classes=100, num_batch=1)
        self.width = 32
        self.height = 32

    def download(self):
        if not isfile('cifar-100-python.tar.gz'):
            with DownloadProgress(unit='B', unit_scale=True, miniters=1, desc='CIFAR-100 Dataset') as pbar:
                urlretrieve(
                    'https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz',
                    'cifar-100-python.tar.gz',
                    pbar.hook)
        else:
            print('cifar-100-python.tar.gz already exists')

        if not isdir(self.path):
            with tarfile.open('cifar-100-python.tar.gz') as tar:
                tar.extractall()
                tar.close()
        else:
            print('cifar10 dataset already exists')

    def load_batch(self, batch_id=1):
        with open(self.path + '/train', mode='rb') as file:
            # note the encoding type is 'latin1'
            batch = pickle.load(file, encoding='latin1')

        features = batch['data'].reshape((len(batch['data']), 3, 32, 32)).transpose(0, 2, 3, 1)
        labels = batch['fine_labels']

        return features, labels

    def preprocess_and_save_data(self, valid_ratio=0.1):
        valid_features = []
        valid_labels = []
        flag = True

        features, labels = self.load_batch()

        index_of_validation = int(len(features) * valid_ratio)

        self.save_preprocessed_data(features[:-index_of_validation], labels[:-index_of_validation], 'cifar100_preprocess_train.p')

        valid_features.extend(features[-index_of_validation:])
        valid_labels.extend(labels[-index_of_validation:])

        # preprocess the all stacked validation dataset
        self.save_preprocessed_data(np.array(valid_features), np.array(valid_labels), 'cifar100_preprocess_validation.p')

        # load the test dataset
        with open(self.path + '/test', mode='rb') as file:
            batch = pickle.load(file, encoding='latin1')

        # preprocess the testing data
        test_features = batch['data'].reshape((len(batch['data']), 3, 32, 32)).transpose(0, 2, 3, 1)
        test_labels = batch['fine_labels']

        # Preprocess and Save all testing data
        self.save_preprocessed_data(np.array(test_features), np.array(test_labels), 'cifar100_preprocess_testing.p')

    def batch_features_labels(self, features, labels, batch_size):
        for start in range(0, len(features), batch_size):
            end = min(start + batch_size, len(features))
            yield features[start:end], labels[start:end]

    def load_preprocess_training_batch(self, batch_id, batch_size, scale_to_imagenet=False):
        filename = 'cifar100_preprocess_train.p'
        features, labels = pickle.load(open(filename, mode='rb'))

        if scale_to_imagenet:
            tmpFeatures = []

            for feature in features:
                tmpFeature = skimage.transform.resize(feature, (224, 224), mode='constant')
                tmpFeatures.append(tmpFeature)

            features = tmpFeatures

        return self.batch_features_labels(features, labels, batch_size)

    def load_valid_set(self):
        valid_features, valid_labels = pickle.load(open('cifar100_preprocess_validation.p', mode='rb'))
        tmpValidFeatures = self.convert_to_imagenet_size(valid_features)

        return tmpValidFeatures, valid_labels