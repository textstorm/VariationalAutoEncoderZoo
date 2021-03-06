
import tensorflow as tf
import numpy as np
import utils
import config
import time
import os

from model import VAE, DCVAE

os.environ["CUDA_VISIBLE_DEVICES"] = "1"

def main(args):
  #
  save_dir = os.path.join(args.save_dir, args.model_type)
  img_dir = os.path.join(args.img_dir, args.model_type)
  log_dir = os.path.join(args.log_dir, args.model_type)
  train_dir = args.train_dir

  if not os.path.exists(save_dir):
    os.makedirs(save_dir)
  if not os.path.exists(log_dir):
    os.makedirs(log_dir)
  if not os.path.exists(img_dir):
    os.makedirs(img_dir)

  mnist = utils.read_data_sets(args.train_dir)
  summary_writer = tf.summary.FileWriter(log_dir)
  config_proto = utils.get_config_proto()

  sess = tf.Session(config=config_proto)
  if args.model_type == "vae":
    model = VAE(args, sess, name="vae")
  elif args.model_type == "dcvae":
    model = DCVAE(args, sess, name="dcvae")

  total_batch = mnist.train.num_examples // args.batch_size

  for epoch in range(1, args.nb_epoch + 1):
    print "Epoch %d start with learning rate %f" % (epoch, model.learning_rate.eval(sess))
    print "- " * 50
    epoch_start_time = time.time()
    step_start_time = epoch_start_time
    for i in range(1, total_batch + 1):
      x_batch, y_batch = mnist.train.next_batch(args.batch_size)
      _, loss, loss_rec, loss_kl, global_step, summaries = model.train(x_batch)
      summary_writer.add_summary(summaries, global_step)
      step_start_time = time.time()

      if global_step % args.log_period == 0:
        print "global step %d, loss %.9f, loss_rec %.9f, loss_kl %.9f, time %.2fs" \
            % (global_step, loss, loss_rec, loss_kl, time.time() - step_start_time)
        step_start_time = time.time()

    if args.anneal and epoch >= args.anneal_start:
      sess.run(model.learning_rate_decay_op)

    if epoch % args.save_period == 0:
      z = np.random.normal(size=[100, args.latent_dim])
      if args.model_type == "vae":
        gen_images = np.reshape(model.generate(z), (100, 28, 28, 1))
      elif args.model_type == "dcvae":
        gen_images = np.reshape(model.generate(z, 100), (100, 28, 28, 1))
      utils.save_images(gen_images, [10, 10], os.path.join(img_dir, "sample%s.jpg" % epoch))

  model.saver.save(sess, os.path.join(save_dir, "model.ckpt"))
  print "Model stored...."

if __name__ == "__main__":
  args = config.get_args()
  main(args)