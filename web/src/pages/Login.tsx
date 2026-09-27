import { Form, Head, usePage } from "@inertiajs/react";
import { Button } from "../components/Button";
import { Notice } from "../components/Notice";
import { Field } from "../components/Field";

export default function Login() {
  const { csrfToken } = usePage().props;
  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <Head title="Sign in" />
      <section className="w-full space-y-6 rounded-xl border border-border bg-panel p-8">
        <div className="space-y-2">
          <p className="text-sm text-muted">PYTHON TEMPLATE</p>
          <h1 className="text-2xl font-semibold">Welcome back</h1>
          <p className="text-sm text-muted">Sign in to your workspace.</p>
        </div>
        <Form
          action="/login/"
          method="post"
          headers={{ "X-CSRFToken": csrfToken }}
          className="space-y-4"
        >
          {({ errors, processing }) => (
            <>
              {errors.__all__ && <Notice>{errors.__all__}</Notice>}
              <Field
                id="username"
                name="username"
                label="Username"
                type="text"
                autoComplete="username"
                required
                error={errors.username}
              />
              <Field
                id="password"
                name="password"
                label="Password"
                type="password"
                autoComplete="current-password"
                required
              />
              <Button type="submit" disabled={processing}>
                {processing ? "Signing in…" : "Sign in"}
              </Button>
            </>
          )}
        </Form>
      </section>
    </main>
  );
}
