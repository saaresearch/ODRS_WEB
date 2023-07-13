import json
import os
import yaml
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.conf import settings

from .forms import ProjectForm
from .models import Project, Files, Classes

from .ORDC.ODRS.ODRC.ml_model_optimizer import main


def create_project(request):
    """
    Функция представления для создания нового проекта.

    Args:
        request (HttpRequest): Объект HTTP-запроса.

    Returns:
        HttpResponse: HTTP-ответ с отрендеренным шаблоном.

    """
    project_id = request.GET.get('project_id')

    # Если 'project_id' отсутствует в запросе, проверяем наличие его значения в сессии
    if not project_id:
        project_id = request.session.get('project_id')
    else:
        # Если 'project_id' присутствует в запросе, сохраняем его значение в сессии
        request.session['project_id'] = project_id

    if project_id:
        # Если 'project_id' задан, получаем объект проекта по 'project_id' из базы данных
        try:
            project = Project.objects.get(id=project_id)
        except:
            project = None
    else:
        project = None

    # Получение всех проектов из базы данных
    projects = Project.objects.all()

    if request.method == 'POST':
        # Обработка POST-запроса при создании проекта

        form = ProjectForm(request.POST)
        if form.is_valid():
            # Если форма прошла валидацию, сохраняем проект
            project = form.save()
            # Сохраняем 'project_id' в сессии
            request.session['project_id'] = project.id
            # Перенаправление на страницу загрузки фотографий
            return redirect('upload_files')
    else:
        # Создание пустой формы для создания проекта
        form = ProjectForm()

    # Отображение страницы 'create_project.html' с передачей данных в шаблон
    return render(request, 'create_project.html', {'project': project, 'projects': projects, 'form': form})


def upload_files(request):
    """
    Функция представления для загрузки фотографий в проект.

    Args:
        request (HttpRequest): Объект HTTP-запроса.

    Returns:
        HttpResponse: HTTP-ответ с отрендеренным шаблоном.

    """
    project_id = request.GET.get('project_id')

    # Если 'project_id' отсутствует в запросе, проверяем наличие его значения в сессии
    if not project_id:
        project_id = request.session.get('project_id')
    else:
        # Если 'project_id' присутствует в запросе, сохраняем его значение в сессии
        request.session['project_id'] = project_id

    if not project_id:
        # Если значение 'project_id' не задано, перенаправляем на страницу создания проекта
        return redirect('create_project')

    # Получение объекта проекта по 'project_id' из базы данных
    project = Project.objects.get(id=project_id)
    # Получение всех проектов из базы данных
    projects = Project.objects.all()

    if request.method == 'POST':
        # Обработка POST-запроса при загрузке фотографий

        folder = request.FILES.getlist('folder')
        if folder:
            # Обработка папки с фотографиями
            folder_paths = request.POST.getlist('folder_paths[]')
            folder_name = os.path.dirname(folder_paths[0])

            folder_main = folder_paths[0].replace(' ', '').split("/", 1)[0]

            folder_main_original = folder_main
            print(folder_main)
            # Проверка наличия папки с таким же главным названием в базе данных
            existing_folders = Files.objects.filter(project=project, folder_name__startswith=folder_main)
            if existing_folders.exists():
                # Если папка с таким же главным названием уже существует, создаем новое название папки
                folder_count = existing_folders.count()
                folder_main = f"{folder_main}_{folder_count + 1}"
            else:
                folder_main = f"{folder_main}_{1}"

            # Сохранение главного пути загружаемых файлов
            request.session['selected_folder'] = folder_main
            file = Files(project=project, files=None, folder_name=folder_main)
            file.save()
            folder_id = 0
            for file in folder:
                # Удаление пробелов из названия папок
                folder_name = os.path.dirname(folder_paths[folder_id].replace(' ', '').replace(folder_main_original, folder_main))
                # Создание экземпляра класса 'Files' и сохранение его в базе данных в случае, если такой файл еще не был загружен
                try:
                    existing_file = Files.objects.get(project=project, files=file, folder_name=folder_name)
                except ObjectDoesNotExist:
                    file = Files(project=project, files=file, folder_name=folder_name)
                    file.save()
                folder_id += 1
            # Сохранение выбранной папки в сессии

            # Перенаправление на страницу отображения фотографий
            return redirect('preview')

    # Отображение страницы 'upload_files.html' с передачей данных в шаблон
    return render(request, 'upload_files.html', {'project': project, 'projects': projects})


def save_config_to_file(config):
    """
    Сохраняет конфигурацию в файл.

    Args:
        config (dict): Словарь с конфигурационными данными.

    Returns:
        None

    """
    config_file_path = os.path.join(os.getcwd(), 'autotrain', 'ORDC', 'ODRS', 'ODRC', 'ml_config.yaml')
    with open(config_file_path, 'w') as file:
        yaml.dump(config, file)


def show_files(request):
    # Получение значения параметра 'project_id' из запроса
    project_id = request.GET.get('project_id')

    selected_folder = ''
    if not project_id:
        # Если 'project_id' отсутствует в запросе, проверяем наличие его значения в сессии
        project_id = request.session.get('project_id')
        selected_folder = request.session.get('selected_folder')
    else:
        # Если 'project_id' присутствует в запросе, сохраняем его значение в сессии
        request.session['project_id'] = project_id

    if not project_id:
        # Если значение 'project_id' не задано, перенаправляем на страницу проектов
        return redirect('projects')

    # Получение объекта проекта по 'project_id'
    project = Project.objects.get(id=project_id)
    # Получение всех проектов
    projects = Project.objects.all()

    # Получение выбранной папки из параметра запроса 'folder_name'
    folder_name = request.GET.get('folder_name', None)
    # Получение уникальных имен папок, связанных с проектом
    folders = project.files_set.values_list('folder_name', flat=True).distinct()

    if folder_name:
        # Если задан параметр 'folder_name', фильтруем фотографии проекта по указанной папке
        files = project.files_set.filter(folder_name=folder_name)
        selected_folder = folder_name
    else:
        # В противном случае выводим все фотографии проекта
        files = project.files_set.all()

    # Конфигурация формы
    config = {
        'dataset_path': selected_folder,
        'classes_path': '',
        'GPU': True,
        'speed': 1,
        'accuracy': 10
    }

    if request.method == 'POST':
        # Обработка POST-запроса при отправке формы

        # Получение значения параметра 'folder_name' из POST-запроса, в конец добавляется обозначение конца пути "/",
        # чтобы отсеять схожие названия
        folder_name = request.POST.get('folder_name') + '/'
        print(folder_name)
        print('This is folder')
        # Получение файла из POST-запроса
        file = request.FILES.get('file')
        # Создание экземпляра класса Classes и сохранение его в базу данных
        classes_instance = Classes(project=project, files_classes=file, folder_name=folder_name)
        classes_instance.save()

        # Обновление значений в конфигурации
        config['dataset_path'] = os.path.join(settings.MEDIA_ROOT, 'files', folder_name)
        config['classes_path'] = os.path.join(settings.MEDIA_ROOT, 'classes', folder_name, str(file))

        if request.POST.get('GPU') == 'on':
            config['GPU'] = True
        else:
            config['GPU'] = False

        config['speed'] = int(request.POST.get('speed'))
        config['accuracy'] = int(request.POST.get('accuracy'))
        config['models_array'] = ["yolov5l", "yolov5m", "yolov5n", "yolov5s", "yolov5x",
                                  "yolov7x", "yolov7", "yolov7-tiny", "yolov8x6", "yolov8x",
                                  "yolov8s", "yolov8n", "yolov8m"]

        # Сохранение конфигурации в файл
        save_config_to_file(config)

        # Запуск основной функции main()
        result = main()
        print(result)
        result_data = json.dumps(result)

        # Отображение страницы результатов с передачей результата в шаблон
        return HttpResponseRedirect(f'/results/?result={result_data}')

    # Отображение страницы show_files.html с передачей данных в шаблон
    return render(request, 'show_files.html', {
        'project': project,
        'projects': projects,
        'files': files,
        'folders': folders,
        'selected_folder': selected_folder,
        'config': config,
    })


def results(request):
    """
    Результаты работы скрипта ml_model_optimizer

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.

    """
    # Получение значения параметра 'project_id' из запроса
    project_id = request.GET.get('project_id')

    selected_folder = ''
    if not project_id:
        # Если 'project_id' отсутствует в запросе, проверяем наличие его значения в сессии
        project_id = request.session.get('project_id')
        selected_folder = request.session.get('selected_folder')
    else:
        # Если 'project_id' присутствует в запросе, сохраняем его значение в сессии
        request.session['project_id'] = project_id

    if not project_id:
        # Если значение 'project_id' не задано, перенаправляем на страницу проектов
        return redirect('projects')

    # Получение объекта проекта по 'project_id'
    project = Project.objects.get(id=project_id)
    # Получение всех проектов
    projects = Project.objects.all()
    yolo_dict = {'yolov5': {'Link': 'https://github.com/ultralytics/yolov5', 'Paper': '-',
                            'Additional information': '-',
                            'Access additional YOLOv5 resources:': {
                                'WIKI': 'https://github.com/ultralytics/yolov5/wiki',
                                'Tutorials': 'https://docs.ultralytics.com/yolov5 ',
                                'Docs': 'https://docs.ultralytics.com'
                            }},
                 'yolov7': {'Link': ' https://github.com/WongKinYiu/yolov7',
                            'Paper': 'https://arxiv.org/abs/2207.02696',
                            'Additional information': '-'},
                 'yolov8': {'Link': 'https://github.com/ultralytics/ultralytics',
                            'Paper': 'https://arxiv.org/abs/2207.02696',
                            'Additional information': {
                                'WIKI': 'https://github.com/ultralytics/ultralytics/wiki',
                                'Tutorials': 'https://docs.ultralytics.com/'
                            }
                            },
                 'Faster-vgg16':
                     {'Link': 'https://github.com/jwyang/faster-rcnn.pytorch/tree/f9d984d27b48a067b29792932bcb5321a39c1f09',
                      'Paper': 'https://arxiv.org/abs/1506.01497',
                      'Additional information': '-',
                      },
                 'SSD': {'Link': 'https://github.com/amdegroot/ssd.pytorch/tree/5b0b77faa955c1917b0c710d770739ba8fbff9b7',
                         'Paper': 'https://arxiv.org/abs/1512.02325',
                         'Additional information': '-',
                         }
                 }
    try:
        result = request.GET.get('result')  # Получение значения параметра 'result' из запроса
        result = json.loads(result)
        top_models = result[1]

        for model_key, model_value in top_models.items():
            for yolo_key in yolo_dict.keys():
                if yolo_key.lower() in model_value.lower():
                    top_models[model_key] = {'name': model_value, 'stats': yolo_dict[yolo_key]}

    except:
        result = None

    return render(request, 'results.html', {'result': result, 'project': project, 'projects': projects,})


def projects(request):
    """
    Представление для отображения всех проектов

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.

    """
    project_id = request.GET.get('project_id')
    if not project_id:
        # Если 'project_id' отсутствует в запросе, проверяем наличие его значения в сессии
        project_id = request.session.get('project_id')
    else:
        # Если 'project_id' присутствует в запросе, сохраняем его значение в сессии
        request.session['project_id'] = project_id
    if project_id:
        project = Project.objects.get(id=project_id)
    else:
        project = None
    projects = Project.objects.all()
    return render(request, 'projects.html', {'project': project, 'projects': projects})


def preview(request):
    """
    Представление для отображения предпросмотра загруженных файлов

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.

    """
    selected_folder = request.session.get('selected_folder')
    project_id = request.GET.get('project_id')

    # Если 'project_id' отсутствует в запросе, проверяем наличие его значения в сессии
    if not project_id:
        project_id = request.session.get('project_id')
    else:
        # Если 'project_id' присутствует в запросе, сохраняем его значение в сессии
        request.session['project_id'] = project_id

    if not project_id:
        # Если значение 'project_id' не задано, перенаправляем на страницу создания проекта
        return redirect('create_project')

    # Получение объекта проекта по 'project_id' из базы данных
    project = Project.objects.get(id=project_id)
    # Получение всех проектов из базы данных
    projects = Project.objects.all()
    print(selected_folder + '/')
    if selected_folder:
        queryset = Files.objects.filter(folder_name__startswith=selected_folder + '/')
        folder_dict = {}
        for file in queryset:
            folder_path = file.folder_name
            folder_parts = folder_path.split("/")
            file_name = file.files.name
            current_dict = folder_dict

            for i, folder_part in enumerate(folder_parts):
                if folder_part not in current_dict:
                    current_dict[folder_part] = {}  # Создаем новый вложенный словарь, если его еще нет
                if i == len(folder_parts) - 1:
                    if "files" not in current_dict[folder_part]:
                        current_dict[folder_part]["files"] = []
                    if len(current_dict[folder_part]["files"]) < 10:
                        current_dict[folder_part]["files"].append((file_name))  # Добавляем файл в список файлов текущей папки
                else:
                    if "folders" not in current_dict[folder_part]:
                        current_dict[folder_part]["folders"] = {}
                    current_dict = current_dict[folder_part]["folders"]  # Переходим к следующему вложенному словарю
    else:
        return render(request, 'projects.html')
    # Обработка случая, когда selected_folder не задан

    return render(request, 'preview.html', {'folder_dict': folder_dict, 'projects': projects, 'project':project})  # Перенаправление на страницу проектов


def delete_project(request):
    """
    Функция для удаления проекта.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response.

    """
    project_id = request.GET.get('project_id')
    # Получение объекта проекта
    try:
        project = Project.objects.get(id=project_id)
    # Обработка случая, когда проект не существует
    except Project.DoesNotExist:
        return redirect('projects')  # Перенаправление на страницу проектов

    # Удаление связанных файлов Files
    files = Files.objects.filter(project=project)
    for file in files:
        try:
            file_path = file.files.path
            file.delete()
            os.remove(file_path)
        except:
            print('Файл удален уже')

    # Удаление связанных файлов Classes
    classes = Classes.objects.filter(project=project)
    for cls in classes:
        try:
            cls_path = cls.files_classes.path
            cls.delete()
            os.remove(cls_path)
        except:
            print('Файл удален уже')



    # Выполнение удаления
    project.delete()
    if request.session['project_id']:
        if request.session['project_id'] == project_id:
            del request.session['project_id']

    return redirect('projects')  # Перенаправление на страницу проектов
