import tensorflow as tf
import numpy as np
import operator

def create_VGG_kaggle_model(image_width, image_height, depth=4, p_dropout=0.0,
        num_classes=2):
    """
    Creates a VGG-like model for binary classification
    """
    data_format = "channels_last"
    # Arch from:
    # https://www.kaggle.com/stevenhurwitt/cats-vs-dogs-using-a-keras-convnet
    model = tf.keras.models.Sequential(name="VGGKaggle{}".format(depth))

    # This assumes pooling size is 2
    max_maxpools = np.min(np.ceil(np.log2([image_height, image_width])))

    for i in range(depth):
        model.add(tf.keras.layers.Conv2D(
            filters=32 * 2**i,
            kernel_size=3,
            padding="same",
            activation="relu",
            data_format=data_format,
            input_shape=(image_height, image_width, 3)))
        model.add(tf.keras.layers.Conv2D(
            filters=32 * 2**i,
            kernel_size=3,
            padding="same",
            activation="relu",
            data_format=data_format))
        if i > 2:
            model.add(tf.keras.layers.Conv2D(
                filters=32 * 2**i,
                kernel_size=3,
                padding="same",
                activation="relu",
                data_format=data_format))
        if i < max_maxpools:
            model.add(tf.keras.layers.MaxPooling2D(
                pool_size=(2, 2),
                data_format=data_format))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(
        256,
        activation="relu"))
    if p_dropout > 0.0:
        model.add(tf.keras.layers.Dropout(
            p_dropout))
    model.add(tf.keras.layers.Dense(
        256,
        activation="relu"))
    if p_dropout > 0.0:
        model.add(tf.keras.layers.Dropout(
            p_dropout))
    if num_classes == 2:
        # Can use logistic since binary
        model.add(tf.keras.layers.Dense(
            1,
            activation="sigmoid"))
    else:
        # Can use logistic since binary
        model.add(tf.keras.layers.Dense(
            num_classes,
            activation="softmax"))
    return model

# For ResNet 101 and 152
class Scale(tf.keras.layers.BatchNormalization):
    def __init__(self,
                 axis=-1,
                 momentum=0.9,
                 beta_initializer="zeros",
                 gamma_initializer="ones",
                 **kwargs):
        self.supports_masking=True
        super(Scale, self).__init__(
                axis=axis,
                momentum=momentum,
                beta_initializer=beta_initializer,
                gamma_initializer=gamma_initializer,
                center=None,
                scale=None,
                **kwargs)

def create_ResNet_kaggle_model(image_width, image_height, finetune_top=True,
        p_dropout=0.0, num_classes=2, use_imagenet_weights=True, depth=50):
    input_shape=(image_height, image_width, 3)
    if depth == 50:
        model = tf.keras.applications.resnet50.ResNet50(
                input_shape=input_shape,
                weights="imagenet" if use_imagenet_weights else None,
                include_top=False,
                )
        if not finetune_top:
            print("Freezing top")
            for l in model.layers:
                l.trainable = False
        # Can use logistic since binary
        x = model.output
        x = tf.keras.layers.Flatten()(x)
        if p_dropout > 0.0:
            x = tf.keras.layers.Dropout(p_dropout)(x)
        if num_classes == 2:
            # Can use logistic since binary
            x = tf.keras.layers.Dense(
                1,
                activation="sigmoid")(x)
        else:
            # Can use logistic since binary
            x = tf.keras.layers.Dense(
                num_classes,
                activation="softmax")(x)
        model = tf.keras.models.Model(
                inputs=model.inputs,
                outputs=x,
                )
    elif depth == 101:
        import keras # These models are incompatible with tf.keras
        import resnet # Resnet 101 and 152
        model = resnet.ResNet101(
                input_shape=input_shape,
                weights="imagenet" if use_imagenet_weights else None,
                include_top=False,
                )
        if not finetune_top:
            print("Freezing top")
            for l in model.layers:
                l.trainable = False
        # Can use logistic since binary
        x = model.output
        x = keras.layers.Flatten()(x)
        if p_dropout > 0.0:
            x = keras.layers.Dropout(p_dropout)(x)
        if num_classes == 2:
            # Can use logistic since binary
            x = keras.layers.Dense(
                1,
                activation="sigmoid")(x)
        else:
            # Can use logistic since binary
            x = keras.layers.Dense(
                num_classes,
                activation="softmax")(x)
        model = keras.models.Model(
                inputs=model.inputs,
                outputs=x,
                )
        # Convert to tf.keras
        conversion_filepath = "/tmp/keras_ResNet101.h5"
        model_json = model.to_json()
        model.save_weights(conversion_filepath)
        del model
        # TODO Scale layer is not needed. Should just ignore weights.
        custom_layers = {"Scale": Scale}
        model = tf.keras.models.model_from_json(model_json, custom_layers)
        model.load_weights(conversion_filepath)
    elif depth == 152:
        import keras # These models are incompatible with tf.keras
        import resnet #Resnet 101 and 152
        model = resnet.ResNet152(
                input_shape=input_shape,
                weights="imagenet" if use_imagenet_weights else None,
                include_top=False,
                )
        if not finetune_top:
            print("Freezing top")
            for l in model.layers:
                l.trainable = False
        # Can use logistic since binary
        x = model.output
        x = keras.layers.Flatten()(x)
        if p_dropout > 0.0:
            x = keras.layers.Dropout(p_dropout)(x)
        if num_classes == 2:
            # Can use logistic since binary
            x = keras.layers.Dense(
                1,
                activation="sigmoid")(x)
        else:
            # Can use logistic since binary
            x = keras.layers.Dense(
                num_classes,
                activation="softmax")(x)
        model = keras.models.Model(
                inputs=model.inputs,
                outputs=x,
                )
        # Convert to tf.keras
        conversion_filepath = "/tmp/keras_ResNet152.h5"
        model_json = model.to_json()
        model.save_weights(conversion_filepath)
        del model
        # TODO Scale layer is not needed. Should just ignore weights.
        custom_layers = {"Scale": Scale}
        model = tf.keras.models.model_from_json(model_json, custom_layers)
        model.load_weights(conversion_filepath)
    else:
        raise RuntimeError("Unsupported resnet depth: '{}'."
                           " Current supported values are 50,"
                           " 101, and 152.".format(depth))

    return model
