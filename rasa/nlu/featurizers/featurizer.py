import numpy as np
import scipy.sparse
from typing import Text, Union, Optional

from rasa.nlu.components import Component
from rasa.nlu.constants import VALID_FEATURE_TYPES
from rasa.utils.tensorflow.constants import MEAN_POOLING, MAX_POOLING


class Features:
    def __init__(
        self,
        features: Union[np.ndarray, scipy.sparse.spmatrix],
        type: Text,
        message_attribute: Text,
        origin: Text,
    ):
        self.validate_type(type)

        self.features = features
        self.type = type
        self.origin = origin
        self.message_attribute = message_attribute

    @staticmethod
    def validate_type(type: Text):
        if type not in VALID_FEATURE_TYPES:
            raise ValueError(
                f"Invalid feature type '{type}' used. Valid feature types are: "
                f"{VALID_FEATURE_TYPES}."
            )

    def is_sparse(self):
        return isinstance(self.features, scipy.sparse.spmatrix)

    def is_dense(self):
        return not self.is_sparse()

    def combine_with_features(
        self, additional_features: Optional[Union[np.ndarray, scipy.sparse.spmatrix]]
    ) -> Optional[Union[np.ndarray, scipy.sparse.spmatrix]]:
        if additional_features is None:
            return self.features

        if self.is_dense() and isinstance(additional_features, np.ndarray):
            return self._combine_dense_features(self.features, additional_features)

        if self.is_sparse() and isinstance(additional_features, scipy.sparse.spmatrix):
            return self._combine_sparse_features(self.features, additional_features)

        raise ValueError(f"Cannot concatenate sparse and dense features.")

    @staticmethod
    def _combine_dense_features(
        features: np.ndarray, additional_features: np.ndarray
    ) -> np.ndarray:
        if len(features) != len(additional_features):
            raise ValueError(
                f"Cannot concatenate dense features as sequence dimension does not "
                f"match: {len(features)} != {len(additional_features)}."
            )

        return np.concatenate((features, additional_features), axis=-1)

    @staticmethod
    def _combine_sparse_features(
        features: scipy.sparse.spmatrix, additional_features: scipy.sparse.spmatrix
    ) -> scipy.sparse.spmatrix:
        from scipy.sparse import hstack

        if features.shape[0] != additional_features.shape[0]:
            raise ValueError(
                f"Cannot concatenate sparse features as sequence dimension does not "
                f"match: {features.shape[0]} != {additional_features.shape[0]}."
            )

        return hstack([features, additional_features])


class Featurizer(Component):
    pass


class DenseFeaturizer(Featurizer):
    @staticmethod
    def _calculate_cls_vector(
        features: np.ndarray, pooling_operation: Text
    ) -> np.ndarray:
        # take only non zeros feature vectors into account
        non_zero_features = np.array([f for f in features if f.any()])

        # if features are all zero just return a vector with all zeros
        if non_zero_features.size == 0:
            return np.zeros([1, features.shape[-1]])

        if pooling_operation == MEAN_POOLING:
            return np.mean(non_zero_features, axis=0, keepdims=True)
        elif pooling_operation == MAX_POOLING:
            return np.max(non_zero_features, axis=0, keepdims=True)
        else:
            raise ValueError(
                f"Invalid pooling operation specified. Available operations are "
                f"'{MEAN_POOLING}' or '{MAX_POOLING}', but provided value is "
                f"'{pooling_operation}'."
            )


class SparseFeaturizer(Featurizer):
    pass
