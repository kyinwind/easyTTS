from docx import Document
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory

def split_word_by_heading(docx_file, output_folder):
    """
    按 Word 文档中的标题1或标题2拆分内容为若干个TXT文件。
    如果存在标题2，则文件名为“序号-标题1-标题2”，否则文件名为“序号-标题1”。
    :param docx_file: Word 文档路径（.docx）
    :param output_folder: 输出TXT文件的文件夹路径
    """
    # 打开Word文档
    document = Document(docx_file)
    current_heading1 = None
    current_heading2 = None
    current_content = []
    heading_counter = 1  # 初始化序号计数器

    for paragraph in document.paragraphs:
        # 检查是否是标题1
        if paragraph.style.name == 'Heading 1':
            # 如果当前有内容，保存到文件
            if current_heading2 or current_heading1:
                save_to_txt(heading_counter, current_heading1, current_heading2, current_content, output_folder)
                current_content = []  # 清空内容
                heading_counter += 1  # 更新序号
            current_heading1 = paragraph.text.strip()  # 更新标题1
            current_heading2 = None  # 清空标题2
        # 检查是否是标题2
        elif paragraph.style.name == 'Heading 2':
            # 如果当前有内容，保存到文件
            if current_heading2:
                save_to_txt(heading_counter, current_heading1, current_heading2, current_content, output_folder)
                current_content = []  # 清空内容
                heading_counter += 1  # 更新序号
            current_heading2 = paragraph.text.strip()  # 更新标题2
        else:
            # 添加到当前内容
            current_content.append(paragraph.text.strip().replace("<", "").replace(">", ""))

    # 保存最后一部分内容
    if current_heading1:
        save_to_txt(heading_counter, current_heading1, current_heading2, current_content, output_folder)


def save_to_txt(counter, heading1, heading2, content, output_folder):
    """
    将内容保存为TXT文件，文件名前缀为“序号-标题1-标题2”或“序号-标题1”。

    :param counter: 序号
    :param heading1: 一级标题名称
    :param heading2: 二级标题名称（可为None）
    :param content: 内容列表
    :param output_folder: 输出TXT文件的文件夹路径
    """
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    # 格式化文件名
    if heading2:
        filename = f"{counter}、{heading1}-{heading2}.txt".replace(" ", "_").replace("/", "_")
        filenamewithouttxt = f"{heading1}、{heading2}"
    else:
        filename = f"{counter}、{heading1}.txt".replace(" ", "_").replace("/", "_")
        filenamewithouttxt = f"{heading1}"
    filepath = os.path.join(output_folder, filename)
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        # 第一行写标题
        f.write(filenamewithouttxt + "\n\n")
        # 写入内容
        f.write("\n".join(content))


if __name__ == "__main__":
    # 使用Tkinter选择文件和目录
    Tk().withdraw()  # 隐藏主窗口
    docx_path = askopenfilename(filetypes=[("Word Documents", "*.docx")], title="选择一个Word文档")
    
    if not docx_path:
        print("未选择文件，程序退出。")
    else:
        # 获取源文件所在目录
        output_dir = os.path.dirname(docx_path)
        
        # 运行拆分函数
        split_word_by_heading(docx_path, output_dir)
        print(f"所有文件已保存到目录：{output_dir}")
