import { Form, Head, router, usePage } from "@inertiajs/react";
import type { Note } from "../types";
import { Layout } from "../components/Layout";
import { Button } from "../components/Button";
import { Field } from "../components/Field";

export default function Home({ notes }: { notes: Note[] }) {
  const {
    props: { auth, csrfToken },
    flash,
  } = usePage();
  const user = auth.user;
  if (!user) throw new Error("Home requires an authenticated user");
  return (
    <Layout user={user}>
      <Head title="Workspace" />
      <div className="mb-8 space-y-2">
        <p className="text-sm text-muted">YOUR WORKSPACE</p>
        <h1 className="text-3xl font-semibold">A place to start.</h1>
        <p className="text-sm text-muted">Signed in as {user.username}</p>
      </div>
      <div role="status" className="mb-4 text-sm">
        {flash.messages?.map((item, index) => (
          <p key={index}>{item.message}</p>
        ))}
      </div>
      <section aria-label="Notes" className="max-w-2xl space-y-6">
        <Form
          action="/notes/"
          method="post"
          headers={{ "X-CSRFToken": csrfToken }}
          resetOnSuccess
          className="space-y-3"
        >
          {({ errors, processing }) => (
            <>
              <Field
                multiline
                id="body"
                name="body"
                label="New note"
                required
                maxLength={2000}
                rows={4}
                error={errors.body}
              />
              <Button type="submit" disabled={processing}>
                Add note
              </Button>
            </>
          )}
        </Form>
        {notes.length === 0 ? (
          <p className="text-sm text-muted">
            Your notes will appear here. Only you can see them.
          </p>
        ) : (
          <ul className="space-y-3">
            {notes.map((note) => (
              <li
                key={note.id}
                className="flex items-start justify-between gap-4 rounded-lg border border-border bg-panel p-4"
              >
                <p className="min-w-0 text-sm break-words whitespace-pre-wrap">
                  {note.body}
                </p>
                <Button
                  variant="secondary"
                  onClick={() =>
                    router.post(
                      `/notes/${note.id}/delete/`,
                      {},
                      {
                        headers: { "X-CSRFToken": csrfToken },
                      },
                    )
                  }
                >
                  Delete
                </Button>
              </li>
            ))}
          </ul>
        )}
        <p className="text-xs text-muted">Showing up to 50 recent notes.</p>
      </section>
    </Layout>
  );
}
