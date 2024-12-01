import ffmpeg
import whisper

import os
import tempfile
import warnings
from utils import filename, write_srt



class VideoSubtitleOverlay:
    def __init__(self, model_name="medium", video_path=None, output_dir="uploads_media/subs", output_srt=True):
        self.model_name = model_name
        self.video_path = video_path or 'uploads_media/video/v.mp4'  # Значение по умолчанию
        self.output_dir = output_dir
        self.output_srt = output_srt
        self.model = self.load_model()

        self.subtitles = None

    def load_model(self):
        """Загружает модель Whisper."""
        print("Загружаем модель Whisper...")
        model = whisper.load_model(self.model_name)  # Можно указать другую модель: "tiny", "small", "medium", "large"
        print("Модель успешно загружена.")
        return model

    def transcribe(self):
        """Процесс транскрипции."""
        print(f"Транскрибируем файл {self.video_path}...")
        
        # Извлекаем аудио из видео
        audios = get_audio([self.video_path])

        # Генерируем субтитры
        self.subtitles = get_subtitles(
            audios, self.output_srt, self.output_dir, lambda audio_path: self.model.transcribe(audio_path)
        )

        print(f"Транскрипция завершена. - {self.subtitles}")
        return self.subtitles
    
    def subtitle_adder(self):
        for path, srt_path in self.subtitles.items():
            out_path = os.path.join("uploads_media/subs", f"{filename(path)}.mp4")

            print(f"Adding subtitles to {out_path}...")
            print(f'path: {path}, srt_path: {srt_path}')

            video = ffmpeg.input(path)
            audio = video.audio

            ffmpeg.concat(
                video.filter('subtitles', srt_path, force_style="OutlineColour=&H40000000,BorderStyle=3"), audio, v=1, a=1
            ).output(out_path).run(quiet=False, overwrite_output=True)

            print(f"Saved subtitled video to {os.path.abspath(out_path)}.")




def get_audio(paths):

    temp_dir = tempfile.gettempdir()
    audio_paths = {}

    for path in paths:
        print(f"Extracting audio from {filename(path)}...")
        output_path = os.path.join(temp_dir, f"{filename(path)}.wav")

        ffmpeg.input(path).output(
            output_path,
            acodec="pcm_s16le", ac=1, ar="16k"
        ).run(quiet=False, overwrite_output=True)

        audio_paths[path] = output_path

    return audio_paths


def get_subtitles(audio_paths: list, output_srt: bool, output_dir: str, transcribe: callable):
    subtitles_path = {}

    for path, audio_path in audio_paths.items():
        srt_path = output_dir if output_srt else tempfile.gettempdir()
        srt_path = os.path.join(srt_path, f"{filename(path)}.srt")
        
        print(
            f"Generating subtitles for {filename(path)}... This might take a while."
        )

        warnings.filterwarnings("ignore")
        result = transcribe(audio_path)
        warnings.filterwarnings("default")

        with open(srt_path, "w", encoding="utf-8") as srt:
            write_srt(result["segments"], file=srt)

        subtitles_path[path] = srt_path

    return subtitles_path

if __name__ == "__main__":
    transcription = VideoSubtitleOverlay()
    transcription.transcribe()
    transcription.subtitle_adder()
