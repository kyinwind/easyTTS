import os
import re
import azure.cognitiveservices.speech as speechsdk
from tkinter import Tk
from tkinter.filedialog import askdirectory
from pydub import AudioSegment

# 配置 API 密钥和区域
speech_key = ""
service_region = ""
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

# 配置语音属性（如语音风格、音频格式）
speech_config.speech_synthesis_voice_name = "zh-CN-YunyangNeural"  # 替换为你需要的语音名称
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3)

def synthesize_text_to_mp3(text, output_path, speed="0.8"):
    """
    将文本合成语音并保存为 MP3 文件，支持语速调整。
    :param text: 输入的文本内容
    :param output_path: 输出 MP3 文件路径
    :param speed: 语速（默认值为 "1.0"，可以设置为 "0.5"（慢速）或 "2.0"（快速）等）
    """
    # 使用 SSML 调整语速
    ssml_template = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
           xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-CN">
        <voice name="zh-CN-YunyangNeural">
            <prosody rate="{speed}">
                {text}
            </prosody>
        </voice>
    </speak>
    """
    
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # 使用 SSML 调用 TTS
    result = synthesizer.speak_ssml_async(ssml_template).get()
    file_name = os.path.basename(output_path)
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"文件{file_name}生成成功: {output_path}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"文件{file_name}合成被取消: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"错误详细信息: {cancellation_details.error_details}")

def split_text(text, max_length=1000):
    """
    将长文本拆分为多个段落，每段不超过指定长度。
    :param text: 输入的文本内容
    :param max_length: 每段文本的最大长度
    :return: 拆分后的文本列表
    """
    paragraphs = []
    while len(text) > max_length:
        split_index = text.rfind("。", 0, max_length)  # 尽量在句号处拆分
        if split_index == -1:
            split_index = max_length
        paragraphs.append(text[:split_index + 1])
        text = text[split_index + 1:]
    if text:
        paragraphs.append(text)
    return paragraphs

def merge_audio_files(file_list, output_file):
    """
    合并多个 MP3 文件，保持采样率为 16 kHz，比特率为 128 kbps，单声道。
    :param files: 要合并的 MP3 文件路径列表
    :param output_file: 合并后的输出文件路径
    """
    # 加载第一个音频文件
    combined_audio = AudioSegment.from_file(file_list[0])

    # 逐一加载并合并音频文件
    for file in file_list[1:]:
        audio = AudioSegment.from_file(file)
        combined_audio += audio

    # 设置导出格式和参数
    #combined_audio = combined_audio.set_frame_rate(16000)  # 16 kHz
    #combined_audio = combined_audio.set_channels(1)       # 单声道
    #combined_audio = combined_audio.set_sample_width(2)   # 保持与 MP3 格式兼容的采样宽度

    # 导出为 MP3 文件，设置比特率
    combined_audio.export(output_file, format="mp3", bitrate="128k")
    print(f"音频已成功合并并保存到: {output_file}")

def extract_number(file_name):
    # 用正则表达式提取文件名中的第一个数字
    match = re.search(r'\d+', file_name)
    return int(match.group()) if match else float('inf')  # 如果没有数字，放在最后

def process_txt_files_in_directory(input_directory, output_directory, speed="0.8"):
    """
    遍历指定目录下的所有 `.txt` 文件，并生成对应的 MP3 文件，支持语速调整。
    """
    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)

    # 遍历目录下的所有 `.txt` 文件
    for file_name in sorted(os.listdir(input_directory), key=extract_number):
        if file_name.endswith(".txt"):
            input_file_path = os.path.join(input_directory, file_name)
            base_name = file_name.replace(".txt", "")
            final_output_file = os.path.join(output_directory, f"{base_name}.mp3")

            # 检查同名 MP3 文件是否已存在且非空
            if os.path.exists(final_output_file) and os.path.getsize(final_output_file) > 0:
                print(f"文件已存在且非空，跳过生成: {final_output_file}")
                continue
            
            print(f"<------------开始处理文件: {final_output_file}")
            # 读取文本内容
            with open(input_file_path, "r", encoding="utf-8") as file:
                text = file.read()

            # 拆分长文本
            paragraphs = split_text(text, max_length=1500)
            temp_files = []

            # 为每个段落生成 MP3 文件
            for i, paragraph in enumerate(paragraphs):
                temp_file = os.path.join(output_directory, f"{base_name}_part{i + 1}.mp3")
                synthesize_text_to_mp3(paragraph, temp_file, speed=speed)
                temp_files.append(temp_file)

            # 合并生成的 MP3 文件
            final_output_file = os.path.join(output_directory, f"{base_name}.mp3")
            merge_audio_files(temp_files, final_output_file)

            # 清理临时文件
            for temp_file in temp_files:
                os.remove(temp_file)
                print(f"已删除临时文件: {temp_file}")
            print(f"MP3 文件生成完成: {final_output_file}------------>")

# 主程序
if __name__ == "__main__":
    # 使用 tkinter 弹出窗口让用户选择输入目录
    Tk().withdraw()  # 隐藏主窗口
    input_dir = askdirectory(title="请选择包含 .txt 文件的目录")

    # 检查用户是否选择了目录
    if not input_dir:
        print("未选择任何目录，程序退出。")
    else:
        print(f"选择的目录: {input_dir}")

        # 用户输入语速
        speed = "0.8"

        # 设置输出目录
        #output_dir = os.path.join(input_dir, "output_mp3_files")
        output_dir = input_dir
        # 执行批量处理
        process_txt_files_in_directory(input_dir, output_dir, speed=speed)
        print(f"所有文件已处理，MP3 文件保存在: {output_dir}")
