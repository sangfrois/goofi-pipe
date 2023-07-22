from goofi import data_in, data_out, manager, normalization, processors

if __name__ == "__main__":
    # configure the pipeline through the Manager class
    mngr = manager.Manager(
        data_in={
            "muse": data_in.EEGRecording.make_eegbci()
            # "muse": data_in.EEGStream("Muse00:55:DA:B5:AB:F7")
        },
        processors=[
            processors.LempelZiv(),
            processors.Biotuner(channels={"muse": ["AF7"]}),
            processors.Biocolor(channels={"muse": ["AF7"]}),
            processors.Bioelements(channels={"muse": ["AF7"]}),
            processors.TextGeneration(
                processors.TextGeneration.TXT2IMG_PROMPT,
                "/muse/biocolor/ch0_peak0_name",
                "/muse/bioelements/ch0_bioelements",
                "/muse/bioelements/ch0_types",
            ),
            processors.TextGeneration(
                processors.TextGeneration.POETRY_PROMPT,
                "/muse/biocolor/ch0_peak0_name",
                "/muse/bioelements/ch0_bioelements",
                "/muse/bioelements/ch0_types",
                model="gpt-4",
                keep_conversation=True,
                read_text=True,
                label="poetry",
                update_frequency=1 / 20,
            ),
            processors.ImageGeneration(
                "/muse/text-generation",
                model=processors.ImageGeneration.STABLE_DIFFUSION,
                img2img=True,
                img_size=(1280, 720),
                inference_steps=15,
                update_frequency=1 / 6,
            ),
        ],
        normalization=normalization.StaticBaselineNormal(30),
        data_out=[
            data_out.OSCStream("127.0.0.1", 5005),
            # data_out.PlotProcessed(),
        ],
    )

    # start the pipeline
    mngr.run()
