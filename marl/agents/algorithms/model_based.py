from . import Base_Actor_Critic_Algorithm
import tensorflow as tf
import sonnet as snt

class Model_Based_Algorithm(Base_Actor_Critic_Algorithm):
    """Simple model-based actor critic agent"""

    def save(self, path): pass
    def restore(self, path): pass

    def __init__(self, discount_factor=0.9, **kwargs):
        super(Model_Based_Algorithm, self).__init__(**kwargs)

        self.discount_factor = discount_factor

        state_size = 64

        self.state_encoder = snt.Sequential([
            snt.Linear(128),
            tf.nn.relu,
            snt.Linear(64),
            tf.nn.swish,
            snt.Linear(state_size)
        ])
        
        self.state_decoder = snt.Sequential([
            snt.Linear(128),
            tf.nn.relu,
            snt.Linear(64),
            tf.nn.swish,
            snt.Linear(state_size)
        ])
        
        self.policy = snt.Sequential([
            snt.Linear(64),
            tf.nn.swish,
            snt.Linear(64),
            tf.nn.swish,
            snt.Linear(self.action_space.shape[0])
        ])

        @tf.function
        def compute_logits(x):
            return x/(x-1)
        self.reward_estimator = snt.Sequential([
            snt.Linear(32),
            tf.nn.swish,
            snt.Linear(16),
            #inverse logits [0,1) -> (-inf, inf),
            compute_logits,
            snt.Sum(),
        ])
        
        self.predictor = snt.Sequential([
            snt.Linear(64),
            tf.nn.swish,
            snt.Linear(64),
            tf.nn.swish,
            snt.Linear(self.observation_space.shape[0])
        ])
    
    def act(self, obs):
        obs = tf.expand_dims(obs, 0) #create a batch of size 1
        state = self.state_encoder(obs)
        action = self.policy(state)
        return action[0] #this is the only output in the batch
    
    def pred(self, obs, a):
        obs = tf.expand_dims(obs, 0) #create a batch of size 1
        a = tf.expand_dims(a, 0) #create a batch of size 1
        pred = self.predictor(tf.concat([obs, a], axis=-1))
        return pred[0] #this is the only output in the batch

    def estimate_reward(self, obs, a):
        return self.reward_estimator(
            tf.concat([obs, a], axis=-1))

    def _imag_rollout(self, obs, a, T=10):
        """generates rollout for T steps
        
        return: returns list of imagined (obs, a) tuples
                INCLUDING the given (obs, a) pair"""
        imag_obs = [obs]
        imag_a = [a]
        for tau in range(T):
            imag_obs.append(self.pred(imag_obs[-1], imag_a[-1]))
            imag_a.append(self.act(imag_obs[-1])) #the last imag_a computation is superfluous
        return [{"obs": i_o, "a": i_a}
                for i_o, i_a in zip(imag_obs, imag_act)]]

    def q_fn(self, obs=None, a=None, T=10, rollout=None):
        """computes Q-value of (obs,a) for T steps.
        alternatively, you can supply a precomputed rollout
        (but not both (obs,a) T and rollout)"""
        if rollout is None:
            assert obs is not None and a is not None
            rollout = self._imag_rollout(obs, a, T)
        else:
            assert obs is None and a is None

        discounted_sum = 0.
        for tau, step in enumerate(rollout, start=0):
            discounted_sum += (self.discount_factor ** tau) * \
                self.estimate_reward(step["obs"], step["a"])
        return discounted_sum

    def train(self, data):
        """data: list of (obs, a, r, done, info) tuples"""
        c_recon = 0.2 #reconstructive accuracy importance
        c_pred_roll = 1.0 #predictive rollout accuracy importance
        c_r = 0.5 #reward function accuarcy importance
        c_q_fn = 1.0 #Q function accuracy importance

        pred_loss = []
        policy_loss = []
        for t in range(len(data)):
            obs, a, r, done, info = data[t]
            rollout_len = 10
            rollout = self._imag_rollout(obs, a, T=rollout_len)

            #min reconstructive loss
            pred_loss = c_recon * tf.keras.losses.mse(
                y_true=obs,
                y_pred=tf.squeeze(
                    self.state_decoder(
                    self.state_encoder(
                        tf.expand_dims(obs, 0)
                    )), axis=0)
            )
            #minimize predictive trajectory deviation
            @tf.function
            def frechet_dist(true_seq, pred_seq):
                """computes frechet distance between
                sequences with length of shortest sequence"""
                distances = [
                    tf.keras.losses.mse(
                        y_true=true_seq_elem,
                        y_pred=pred_seq_elem
                    )
                    for true_seq_elem, pred_seq_elem
                    in zip(true_seq, pred_seq)]
                beta = 1e2
                return tf.reduce_sum(tf.nn.softmax(
                    beta*distances), axis=-1)
            pred_loss += c_pred_roll * frechet_dist(
                true_seq = [obs for obs, _, _, _, _ in data[t:]],
                pred_seq = [step["obs"] for step in rollout]
            )
            #maximize reward estimation accuracy
            pred_loss += c_r * tf.keras.losses.mse(
                y_true=r,
                y_pred=self.estimate_reward(obs, a)
            )
            #maximize reward estimation accuracy
            rollout_to_end = rollout[t:]
            if len(rollout_to_end) > rollout_len:
                rollout_to_end = rollout_to_end[:rollout_len]
            pred_loss += c_q_fn * tf.keras.losses.mse(
                y_true=sum([r for _, _, r, _, _ in data[t:]]),
                y_pred=self.q_fn(rollout=rollout_to_end)
            )
            # maximize Q-function over policy space
            policy_loss = [self.q_fn(rollout=rollout)]
        #TODO OPTIMIZE WITH RESPECT TO BELOW:
        #TODO min `sum(pred_loss)` on {pred, encoder, decoder}.trainable_vars
        #TODO min `sum(policy_loss)` on policy.trainable_vars