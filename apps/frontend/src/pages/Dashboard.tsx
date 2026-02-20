import EmailListItem from "@/components/EmailListItem";
import ReplyModal from "@/components/ReplyModal";
import { Email } from "@/features/emails/types";
import {
  useEmailCount,
  useEmails,
  useGenerateReply,
  useSendReply,
  useSyncEmails,
  useUnsubscribe,
} from "@/hooks/emailHooks";
import { useEmailStore } from "@/store/emailStore";

const Dashboard = () => {
  const { data: emails, isLoading } = useEmails();
  const { data: count } = useEmailCount();
  const syncMutation = useSyncEmails();
  const generateReplyMutation = useGenerateReply();
  const sendReplyMutation = useSendReply();
  const unsubscribeMutation = useUnsubscribe();
  const { openReply } = useEmailStore();

  const handleReply = async (email: Email) => {
    const draft = await generateReplyMutation.mutateAsync(email.id);
    openReply(email, draft.reply_text);
  };

  const handleSend = async (replyText: string, emailId: number) => {
    await sendReplyMutation.mutateAsync({ emailId, replyText });
  };

  return (
    <main className="px-6 pb-12">
      <section className="card p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-white/60 text-sm">Total emails</p>
            <p className="text-4xl font-display font-semibold">{count?.total ?? 0}</p>
          </div>
          <button
            className="px-5 py-3 rounded-full bg-white/10 hover:bg-white/20"
            onClick={() => syncMutation.mutate()}
          >
            {syncMutation.isPending ? "Syncing..." : "Sync Inbox"}
          </button>
        </div>
      </section>

      <section className="grid gap-4">
        {isLoading && <p className="text-white/60">Loading emails...</p>}
        {!isLoading && emails?.length === 0 && (
          <p className="text-white/60">No emails yet. Run a sync to fetch data.</p>
        )}
        {emails?.map((email) => (
          <EmailListItem
            key={email.id}
            email={email}
            onReply={() => handleReply(email)}
            onUnsubscribe={() => unsubscribeMutation.mutate(email.id)}
          />
        ))}
      </section>

      <ReplyModal onSend={handleSend} isSending={sendReplyMutation.isPending} />
    </main>
  );
};

export default Dashboard;
