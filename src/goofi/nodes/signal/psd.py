import numpy as np
from numpy.fft import fft, fftfreq
from scipy.signal import welch

from goofi.data import Data, DataType
from goofi.node import Node
from goofi.params import FloatParam, IntParam, StringParam


class PSD(Node):
    def config_input_slots():
        return {"data": DataType.ARRAY}

    def config_output_slots():
        return {"psd": DataType.ARRAY,
                "phase": DataType.ARRAY}

    def config_params():
        return {
            "psd": {
                "method": StringParam("welch", options=["fft", "welch"]),
                "noverlap": IntParam(0, 0, 10000),
                "precision": FloatParam(0.1, 0.01, 10.0),
                "f_min": FloatParam(1.0, 0.01, 9999.0),
                "f_max": FloatParam(60.0, 1.0, 10000.0),
                "smooth_welch": IntParam(1, 1, 10),
            }
        }

    def process(self, data: Data):
        if data is None or data.data is None:
            return None

        if data.data.ndim not in [1, 2]:
            raise ValueError("Data must be 1D or 2D")

        method = self.params["psd"]["method"].value
        noverlap = self.params["psd"]["noverlap"].value
        precision = self.params["psd"]["precision"].value
        f_min = self.params["psd"]["f_min"].value  # Get the min frequency
        f_max = self.params["psd"]["f_max"].value  # Get the max frequency
        smooth = self.params["psd"]["smooth_welch"].value

        sfreq = data.meta["sfreq"]
        nperseg = int(sfreq / precision)
        nfft = nperseg / smooth
        if method == "fft":
            freq = fftfreq(data.data.shape[-1], 1 / sfreq)
            fft_result = fft(data.data, axis=-1)
            psd = np.abs(fft_result)
            phase = np.angle(fft_result)
        elif method == "welch":
            if data.data.ndim == 1:
                freq, psd = welch(data.data, fs=sfreq, nperseg=nperseg, nfft=nfft, noverlap=noverlap)
            else:  # if 2D
                psd = []
                for row in data.data:
                    f, p = welch(row, fs=sfreq, nperseg=nperseg, nfft=nfft, noverlap=noverlap)
                    psd.append(p)
                freq = f
                psd = np.array(psd)
            phase=np.zeros(psd.shape)

        # prepare metadata
        meta = data.meta.copy()

        # Selecting the range of frequencies
        valid_indices = np.where((freq >= f_min) & (freq <= f_max))[0]
        freq = freq[valid_indices]
        if data.data.ndim == 1:
            psd = psd[valid_indices]
            phase = phase[valid_indices]
            meta["channels"]["dim0"] = freq.tolist()
        else:  # if 2D
            psd = psd[:, valid_indices]
            phase = phase[:, valid_indices]
            meta["channels"]["dim1"] = freq.tolist()

        return {"psd": (psd, meta), "phase": (phase, meta)}