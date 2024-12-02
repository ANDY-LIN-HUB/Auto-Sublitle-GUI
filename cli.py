import ffmpeg
import whisper

import os
import tempfile
import warnings
from utils import filename, write_srt




class VideoSubtitleOverlay:
    def __init__(self, model_name: str, video_path: str, output_dir: str, output_srt:bool):
        self.model_name = model_name
        self.video_path = video_path
        self.output_dir = output_dir
        self.output_srt = output_srt
        self.model = model

        self.subtitles = None

    def transcribe(self):
        """Процесс транскрипции."""

        print(f"Загрузка модели Whisper: {model}...")
        self.model = whisper.load_model(model)
        print("Модель Whisper успешно загружена.")

        print(f"Транскрибируем файл {self.video_path}...")
        
        # Извлекаем аудио из видео
        audios = get_audio([self.video_path])

        # Генерируем субтитры
        self.subtitles = get_subtitles(
            audios, self.output_srt, self.output_dir, lambda audio_path: self.model.transcribe(audio_path)
        )

        print(f"Транскрипция завершена. - {self.subtitles}")
        return self.subtitles
    
    def subtitle_adder(self, input_video = None, input_sublitles = None):
        
        if input_video and input_sublitles:
            self.subtitles = {input_video : input_sublitles}
            print(self.subtitles)
        

        if self.subtitles:
            for path, srt_path in self.subtitles.items():
                out_path = os.path.join("uploads_media/subs", f"{filename(path)}.mp4")

                print(f"Adding subtitles to {out_path}...")
                print(f'path: {path}, srt_path: {srt_path}')

                video = ffmpeg.input(path)
                audio = video.audio
                try:
                    ffmpeg.concat(
                        video.filter('subtitles', srt_path, force_style="OutlineColour=&H40000000,BorderStyle=1,MarginV=50"), audio, v=1, a=1
                    ).output(out_path).run(quiet=False, overwrite_output=True)
                    print(f"Saved subtitled video to {os.path.abspath(out_path)}.")
                except Exception as e: 
                    print(e)
                
        else: 
            print(f"Ошибка задания путей. Subtitles = {self.subtitles}")




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

    model = "medium" # "tiny", "small", "medium", "large"
    video_path = "uploads_media/video/v.mp4"
    output_dir = "uploads_media/subs"
    sub_path = "uploads_media/subs/v.srt"
    output_str = True

    transcription = VideoSubtitleOverlay(model, video_path, output_dir, output_str)
    # transcription.transcribe()
    transcription.subtitle_adder(video_path, sub_path)
