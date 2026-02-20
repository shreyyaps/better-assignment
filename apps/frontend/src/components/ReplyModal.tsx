import { useEmailStore } from "@/store/emailStore";

type ReplyModalProps = {
  onSend: (replyText: string, emailId: number) => void;
  isSending?: boolean;
};

const ReplyModal = ({ onSend, isSending }: ReplyModalProps) => {
  const { selectedEmail, isReplyOpen, draftText, closeReply, setDraftText } = useEmailStore();

  if (!isReplyOpen || !selectedEmail) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="card p-6 w-full max-w-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-display">Reply Draft</h2>
          <button className="text-white/70 hover:text-white" onClick={closeReply}>
            Close
          </button>
        </div>
        <textarea
          className="w-full min-h-[200px] bg-white/5 rounded-xl p-4 text-white/90 focus:outline-none"
          value={draftText}
          onChange={(event) => setDraftText(event.target.value)}
        />
        <div className="flex justify-end mt-4 gap-2">
          <button
            className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20"
            onClick={closeReply}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 rounded-full bg-ember text-black font-semibold"
            onClick={() => onSend(draftText, selectedEmail.id)}
            disabled={isSending}
          >
            {isSending ? "Sending..." : "Send Reply"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReplyModal;
