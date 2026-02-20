import { Email } from "@/features/emails/types";

const importanceStyles: Record<Email["importance"], string> = {
  high: "bg-red-500/20 text-red-300",
  medium: "bg-yellow-500/20 text-yellow-200",
  low: "bg-emerald-500/20 text-emerald-200",
};

type EmailListItemProps = {
  email: Email;
  onReply: () => void;
  onUnsubscribe: () => void;
};

const EmailListItem = ({ email, onReply, onUnsubscribe }: EmailListItemProps) => {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-white/60 text-sm">{email.sender || "Unknown sender"}</p>
          <h3 className="text-lg font-semibold">{email.subject || "(No subject)"}</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs ${importanceStyles[email.importance]}`}>
            {email.importance.toUpperCase()}
          </span>
          {email.is_spam && (
            <span className="px-3 py-1 rounded-full text-xs bg-white/10 text-white/70">
              SPAM
            </span>
          )}
        </div>
      </div>
      <p className="text-white/70 text-sm">{email.snippet}</p>
      <div className="flex gap-2">
        <button
          className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-sm"
          onClick={onReply}
        >
          Reply
        </button>
        <button
          className="px-4 py-2 rounded-full border border-white/10 text-sm hover:border-white/30"
          onClick={onUnsubscribe}
        >
          Unsubscribe
        </button>
      </div>
    </div>
  );
};

export default EmailListItem;
