# test.py

import numpy as np
import os
import tensorflow as tf
import cv2
import glob

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from distutils.version import StrictVersion

# module level variables ##############################################################################################
TEST_IMAGE_DIR = os.getcwd() +  "/test_images"
FROZEN_INFERENCE_GRAPH_LOC = os.getcwd() + "/exported_model/frozen_inference_graph.pb"
LABELS_LOC = os.getcwd() + "/training_data/" + "label_map.pbtxt"
NUM_CLASSES = 3

#######################################################################################################################
def main():
    print("starting program . . .")

    if not checkIfNecessaryPathsAndFilesExist():
        return
    # end if

    # this next comment line is necessary to avoid a false PyCharm warning
    # noinspection PyUnresolvedReferences
    if StrictVersion(tf.__version__) < StrictVersion('1.5.0'):
        raise ImportError('Please upgrade your tensorflow installation to v1.5.* or later!')
    # end if

    # load a (frozen) TensorFlow model into memory
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(FROZEN_INFERENCE_GRAPH_LOC, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
        # end with
    # end with

    # Loading label map
    # Label maps map indices to category names, so that when our convolution network predicts `5`,
    # we know that this corresponds to `airplane`.  Here we use internal utility functions,
    # but anything that returns a dictionary mapping integers to appropriate string labels would be fine
    label_map = label_map_util.load_labelmap(LABELS_LOC)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    imageFilePaths = []

    for child_dir in [f.path for f in os.scandir(TEST_IMAGE_DIR) if f.is_dir()]:
        for imageFileName in os.listdir(child_dir):
            if imageFileName.endswith(".jpg"):
                imageFilePaths.append(child_dir + "/" + imageFileName)


    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            for image_path in imageFilePaths:

                image_np = cv2.imread(image_path)

                if image_np is None:
                    print("error reading file " + image_path)
                    continue
                # end if

                # Definite input and output Tensors for detection_graph
                image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
                # Each box represents a part of the image where a particular object was detected.
                detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
                # Each score represent how level of confidence for each of the objects.
                # Score is shown on the result image, together with the class label.
                detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
                detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
                num_detections = detection_graph.get_tensor_by_name('num_detections:0')

                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(image_np, axis=0)
                # Actual detection.
                (boxes, scores, classes, num) = sess.run(
                    [detection_boxes, detection_scores, detection_classes, num_detections],
                    feed_dict={image_tensor: image_np_expanded})

                # print out, what was predicted

                objects = []
                threshold = 0.2  # in order to get higher percentages you need to lower this number; usually at 0.01 you get 100% predicted objects
                for index, value in enumerate(classes[0]):
                    object_dict = {}
                    if scores[0, index] > threshold:
                        object_dict[(category_index.get(value)).get('name').encode('utf8')] = scores[0, index]
                        objects.append(object_dict)
                # objects: [{b'mouse': 0.971244}]
                # print(objects)
                # we assume there is only one object found:
                try:
                    classification = list(objects[0].keys())[0]
                    score = round(objects[0][classification] * 100, 2)
                    classification = classification.decode("utf-8")
                except:
                    classification = "-"
                    score = "-"
                print("%s : %s : %r " % (image_path, classification, score))

                # Visualization of the results of a detection.
                vis_util.visualize_boxes_and_labels_on_image_array(image_np,
                                                                   np.squeeze(boxes),
                                                                   np.squeeze(classes).astype(np.int32),
                                                                   np.squeeze(scores),
                                                                   category_index,
                                                                   use_normalized_coordinates=True,
                                                                   line_thickness=8)
                resized_image = cv2.resize(image_np, (0, 0), fx=0.8, fy=0.8)
                cv2.imshow("image_np", resized_image)
                cv2.waitKey()
            # end for
        # end with
    # end with
# end main

#######################################################################################################################
def checkIfNecessaryPathsAndFilesExist():
    if not os.path.exists(TEST_IMAGE_DIR):
        print('ERROR: TEST_IMAGE_DIR "' + TEST_IMAGE_DIR + '" does not seem to exist')
        return False
    # end if

    # ToDo: check here that the test image directory contains at least one image

    if not os.path.exists(FROZEN_INFERENCE_GRAPH_LOC):
        print('ERROR: FROZEN_INFERENCE_GRAPH_LOC "' + FROZEN_INFERENCE_GRAPH_LOC + '" does not seem to exist')
        print('was the inference graph exported successfully?')
        return False
    # end if

    if not os.path.exists(LABELS_LOC):
        print('ERROR: the label map file "' + LABELS_LOC + '" does not seem to exist')
        return False
    # end if

    return True
# end function

#######################################################################################################################
if __name__ == "__main__":
    main()
