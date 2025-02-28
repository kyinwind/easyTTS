from gradio_client import Client, file

import os
import re
from tkinter import Tk
from tkinter.filedialog import askdirectory
from pydub import AudioSegment


client = Client("http://localhost:9872/")

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

def synthesize_text_to_mp3(text, output_path, speed="0.8",cankao_file="",cankao_txt=""):
    #print("文件是否存在:", os.path.exists(cankao_file))
    #print("cankao_file 类型:", type(cankao_file))
    from gradio_client import handle_file
    #print("file 函数:", file)
    #print(file(cankao_file))
    # 确保传递的 `cankao_file` 是一个字符串路径，而不是文件对象
    ref_audio_path = handle_file(cankao_file)
    result = client.predict(
        text= text,
        text_lang="中文",
        ref_audio_path=ref_audio_path,  # 这里修正
        aux_ref_audio_paths=[],
        prompt_text=cankao_txt,
        prompt_lang="中文",
        top_k=5,
        top_p=1,
        temperature=1,
        text_split_method="凑四句一切",
        batch_size=20,
        speed_factor=1,
        ref_text_free=False,
        split_bucket=True,
        fragment_interval=0.3,
        seed=-1,
        keep_random=True,
        parallel_infer=True,
        repetition_penalty=1.35,
        api_name="/inference"
    )
    print(result)
    print(output_path)
    # 从wav文件加载音频数据
    wav_file_path = result[0]
    audio = AudioSegment.from_wav(wav_file_path)
    # 将音频数据导出为mp3格式
    audio.export(output_path, format="mp3")

def merge_audio_files(file_list, output_file):
    """
    合并多个 MP3 文件，保持采样率为 16 kHz，比特率为 128 kbps，单声道。
    :param files: 要合并的 MP3 文件路径列表
    :param output_file: 合并后的输出文件路径
    """
    # 加载第一个音频文件
    combined_audio = AudioSegment.from_file(file_list[0])

    # 逐一加载并合并音频文件
    for audiofile in file_list[1:]:
        audio = AudioSegment.from_file(audiofile)
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

def process_txt_files_in_directory(input_directory, output_directory, speed="0.8",cankao_file="",cankao_txt=""):
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
                synthesize_text_to_mp3(paragraph, temp_file, speed=speed,cankao_file=cankao_file,cankao_txt=cankao_txt)
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
    # 获取脚本所在目录，推导出参考音频的目录
    script_directory = os.path.dirname(os.path.abspath(__file__))
    print("脚本所在目录:", script_directory)
    cankao_dir = os.path.join(script_directory, "cankao")
    # 获取参考音频文件，即参考目录下一个名为cankao.wav的文件
    cankao_file = os.path.join(cankao_dir, "cankao.wav") 
    cankao_txtfile = os.path.join(cankao_dir, "cankao.txt")
    #读出参考文本文件的内容
    with open(cankao_txtfile, "r", encoding="utf-8") as file:
        cankao_text = file.read()
    print("参考音频文件:", cankao_file)
    print("参考文本内容:", cankao_text)
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
        process_txt_files_in_directory(input_dir, output_dir, speed=speed,cankao_file=cankao_file,cankao_txt=cankao_text)
        print(f"所有文件已处理，MP3 文件保存在: {output_dir}")
