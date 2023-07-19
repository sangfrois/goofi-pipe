import time
from typing import Dict, List, Union

from neurofeedback.processors import SignalStd
from neurofeedback.utils import DataIn, DataOut, Normalization, Processor


class Manager:
    """
    Central class to manage an EEG input stream, several processing steps,
    feature normalization and multiple output channels.

    Parameters:
        data_in (List[DataIn]): a list of DataIn channels (e.g. EEGStream, EEGRecording)
        processors (List[Processor]): a list of Processor instances (e.g. PSD, LempelZiv)
        normalization (Normalization): the normalization strategy to apply to the extracted features
        data_out (List[DataOut]): a list of DataOut channels (e.g. OSCStream, PlotProcessed)
        frequency (int): frequency of the data processing loop (-1 to run as fast as possible)
        noise_threshold (float or Dict[str,float]): threshold for detecting if a device is in use
    """

    def __init__(
        self,
        data_in: Dict[str, DataIn],
        processors: List[Processor],
        normalization: Normalization,
        data_out: List[DataOut],
        frequency: int = 10,
        noise_threshold: Union[Dict[str, float], float] = 4,
    ):
        self.data_in = data_in
        self.processors = processors
        self.normalization = normalization
        self.data_out = data_out
        self.noise_threshold = noise_threshold

        # compute signal standard deviation to estimate noise level
        self.std_processor = SignalStd()

        # auxiliary attributes
        self.frequency = frequency
        self.too_slow_count = 0
        self.filling_buffer = len(self.data_in) > 0

    def update(self):
        """
        Fetches new data from the input channels, processes the data and
        outputs the processed data to the output channels.
        """
        # fetch raw data
        if len(self.data_in) > 0 and any(
            d.update() == -1 for d in self.data_in.values()
        ):
            return
        elif self.filling_buffer:
            print("done")
            self.filling_buffer = False

        # process raw data (feature extraction)
        processed, intermediates, normalize_mask = {}, {}, {}

        # assess if the device is in use or just producing noise
        noise_container = {}
        self.std_processor(self.data_in, noise_container, {})
        self.normalization.normalize(noise_container)
        for key in self.data_in.keys():
            if isinstance(self.noise_threshold, dict):
                thresh = self.noise_threshold[key]
            else:
                thresh = self.noise_threshold
            processed[f"/{key}/in-use"] = float(
                noise_container[f"/{key}/signal-std"] < thresh
            )
            normalize_mask[f"/{key}/in-use"] = False

        for processor in self.processors:
            normalize_mask.update(processor(self.data_in, processed, intermediates))

        # extract the features that need normalization
        finished = {
            lbl: feat for lbl, feat in processed.items() if not normalize_mask[lbl]
        }
        unfinished = {
            lbl: feat for lbl, feat in processed.items() if normalize_mask[lbl]
        }

        # normalize extracted features
        self.normalization.normalize(unfinished)
        finished.update(unfinished)
        finished = {lbl: finished[lbl] for lbl in processed.keys()}

        # update data outputs
        for out in self.data_out:
            out.update(self.data_in, finished, intermediates)

    def run(self, n_iterations: int = -1):
        """
        Start the fetching and processing loop and limit the loop to run at a
        constant update rate.

        Parameters:
            n_iterations (int): number of iterations to run the loop for (-1 for infinite)
        """
        print("Filling buffer(s)...", end="")

        last_time = time.time()
        it = 0
        while it != n_iterations:
            # receive, process and output data
            self.update()
            it += 1

            # limit the loop to run at a constant update rate
            if self.frequency > 0:
                # ensure a constant sampling frequency
                current_time = time.time()
                sleep_dur = 1 / self.frequency - current_time + last_time
                if sleep_dur >= 0:
                    time.sleep(sleep_dur)
                else:
                    self.too_slow_count += 1
                    print(
                        f"Processing too slow to run at {self.frequency}Hz"
                        f" ({self.too_slow_count})"
                    )
                last_time = time.time()


if __name__ == "__main__":
    from neurofeedback import data_in, data_out, normalization, processors

    mngr = Manager(
        data_in={
            "file": data_in.EEGRecording.make_eegbci(),
            "pulse": data_in.SerialStream(sfreq=100, buffer_seconds=60),
        },
        processors=[
             processors.PSD(label="delta"),
             processors.PSD(label="theta"),
             processors.PSD(label="alpha"),
             processors.PSD(label="beta"),
             processors.PSD(label="gamma"),
             processors.LempelZiv(),
            # processors.Ratio("/file/alpha", "/file/theta", "alpha/theta"),
            # processors.Pulse(channels={"pulse": ["serial"]})
            processors.Bioelements(channels={"file": ["C3"]}),
            processors.Biocolor(channels={"file": ["C3"]}),
            # processors.TextGeneration(
            #     processors.TextGeneration.POETRY_PROMPT,
            #     "/muse/biocolor/ch0_peak0_name",
            #     "/muse/bioelements/ch0_bioelements",
            #     read_text=True,
            #     keep_conversation=True,
            #     label="poetry",
            # ),

            processors.ImageGeneration(
                "/file/text-generation",
                model=processors.ImageGeneration.STABLE_DIFFUSION,
                inference_steps=10,
                return_format="b64",
            ),
            processors.Biotuner(channels={"file": ["O1", "O2"]}),
        ],
        normalization=normalization.StaticBaselineNormal(duration=30),
        data_out=[
            data_out.OSCStream("127.0.0.1", 5005),
            # data_out.PlotRaw("file"),
            data_out.PlotProcessed(),
        ],
    )

    mngr.run()
